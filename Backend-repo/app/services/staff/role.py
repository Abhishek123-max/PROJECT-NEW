"""Service layer for Staff Role management."""

from typing import List, Optional, Dict, Any
from sqlalchemy import desc, select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import copy

from app.models.core.auth import Role
from app.models.core.user import User
from app.models.facility.menu import Counter
from app.schemas.staff.role import RoleCreate, RoleUpdate
from app.utils.exceptions import InsufficientPermissionsError, RoleHierarchyError

class RoleService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    @staticmethod
    def _has_any_permission_enabled(node: Any) -> bool:
        """
        Recursively check if any permission flag (create/view/edit/delete/import/export)
        is enabled (True) within a nested permissions structure.
        """
        if not isinstance(node, dict):
            return False

        action_keys = {"create", "view", "edit", "delete", "import", "export"}
        # Leaf page object with action keys
        if action_keys.issubset(node.keys()):
            return any(bool(node.get(k, False)) for k in action_keys)

        # Nested object – recurse over children
        return any(RoleService._has_any_permission_enabled(v) for v in node.values())

    @staticmethod
    def _build_feature_tree(
        perms_node: Any,
        template_node: Any,
    ) -> Any:
        """
        Recursively build a feature tree that mirrors DEFAULT_PAGE_PERMISSIONS:
        - For each leaf page (where CRUD/import/export flags live), return a bool:
          True if any permission flag is enabled, otherwise False.
        - For each group (e.g. "Dashboard", "Employees & Roles"), return a dict
          of children with the same structure.
        """
        # Leaf node: use permission flags to compute a single boolean
        action_keys = {"create", "view", "edit", "delete", "import", "export"}
        if isinstance(template_node, dict) and action_keys.issubset(template_node.keys()):
            # Use the actual perms node if provided; otherwise fall back to the template
            source = perms_node if isinstance(perms_node, dict) else template_node
            return RoleService._has_any_permission_enabled(source)

        # Group node: recurse into children
        if not isinstance(template_node, dict):
            return False

        result: Dict[str, Any] = {}
        for key, sub_template in template_node.items():
            sub_perms = {}
            if isinstance(perms_node, dict):
                sub_perms = perms_node.get(key, {})
            result[key] = RoleService._build_feature_tree(sub_perms, sub_template)
        return result

    @staticmethod
    def _sync_default_features_from_permissions(permissions: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a nested default_features mapping from the given permissions dict.
        
        Example shape:
        {
            "Billing & Payment": True/False,
            "Dashboard": {
                "Overview": True/False,
                "Analytics": True/False,
                "Settings": True/False,
            },
            "Employees & Roles": {
                "Role Management": True/False,
                "Employees": True/False,
            },
            ...
        }
        """
        from app.settings.constants import DEFAULT_PAGE_PERMISSIONS
        
        default_features: Dict[str, Any] = {}
        
        for module_name, module_template in DEFAULT_PAGE_PERMISSIONS.items():
            module_perms = permissions.get(module_name, {})
            default_features[module_name] = RoleService._build_feature_tree(
                module_perms,
                module_template,
            )
        
        return default_features

    async def get_role_by_id(self, role_id: int) -> Optional[Role]:
        return await self.db.get(Role, role_id)


    async def get_role_by_name(self, name: str, hotel_id: Optional[int] = None) -> Optional[Role]:
        """
        Fetch a role by name scoped to a hotel (or global if hotel_id is None).
        """
        query = select(Role).filter(Role.name == name)
        if hotel_id is None:
            query = query.filter(Role.hotel_id.is_(None))
        else:
            query = query.filter(Role.hotel_id == hotel_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all_roles(self) -> List[Role]:
        result = await self.db.execute(select(Role).order_by(desc(Role.id)))
        return list(result.scalars().all())

    async def get_roles_created_by(self, user_id: int) -> List[Role]:
        """Return roles created by the user plus default roles."""
        result = await self.db.execute(
            select(Role)
            .where((Role.created_by == user_id) | (Role.is_default.is_(True)))
            .order_by(desc(Role.id))
        )
        return list(result.scalars().all())

    async def get_roles_by_hotel(self, hotel_id: int) -> List[Role]:
        """
        Return distinct roles that are currently assigned to users in the
        specified hotel. Attaches users to each role in the result.
        """
        from sqlalchemy.orm import selectinload
        role_ids_for_hotel = select(User.role_id).where(User.hotel_id == hotel_id)
        query = (
            select(Role)
            .options(selectinload(Role.users))
            .where(
                ((Role.hotel_id == hotel_id) | (Role.id.in_(role_ids_for_hotel)))
                & (Role.is_default.is_(False))
            )
            .distinct(Role.id)
            .order_by(desc(Role.id))
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_all_roles_with_creator(self) -> List[Role]:
        """
        Fetches all roles and eagerly loads the 'creator' relationship.
        This is the key fix for the 'creator_name: null' problem.
        """
        query = select(Role).options(selectinload(Role.creator)).order_by(Role.level)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_role(self, role_data: RoleCreate, creator: User) -> Role:
        if not creator.role or creator.role.level < role_data.level:
            raise RoleHierarchyError("You cannot create a role with a level equal to or higher than your own.")

        # Resolve hotel scope: explicit hotel_id or creator's hotel
        resolved_hotel_id = role_data.hotel_id or getattr(creator, "hotel_id", None)

        existing_role = await self.get_role_by_name(role_data.name, resolved_hotel_id)
        if existing_role:
            raise ValueError(f"Role with name '{role_data.name}' already exists.")

        # from app.settings.constants import  DEFAULT_PAGE_PERMISSIONS
       # if role_data.name in DEFAULT_ROLE_FEATURES:
        #    permissions_dict = DEFAULT_PAGE_PERMISSIONS[role_data.name].copy()
       # else:
            # If permissions is missing or empty, fill with a deep copy of the nested module/page template
        from app.settings.constants import DEFAULT_USERS_PERMISSIONS
        if not role_data.permissions:
            permissions_dict = DEFAULT_USERS_PERMISSIONS.copy()
        else:
            permissions_dict = role_data.permissions

        new_role = Role(
            **role_data.dict(exclude={"permissions", "hotel_id"}),
            permissions=permissions_dict,
            created_by=creator.id,
            is_default=False,
            hotel_id=resolved_hotel_id
        )
        self.db.add(new_role)
        await self.db.commit()
        await self.db.refresh(new_role)
        return new_role

    async def update_role(self, role_id: int, update_data: RoleUpdate, updater: User) -> Optional[Role]:
        import copy
        role_to_update = await self.get_role_by_id(role_id)
        if not role_to_update:
            return None
     
        if updater.role.level < role_to_update.level:
            raise RoleHierarchyError("You cannot update a role with a level equal to or higher than your own.")
        
        if bool(role_to_update.is_default):
            raise InsufficientPermissionsError("Default system roles cannot be modified.")

        update_dict = update_data.dict(exclude_unset=True)

        # Explicitly handle permissions to ensure correct JSON serialization
        from app.settings.constants import page_permissions_for_role
        if "permissions" in update_dict:
            if not update_data.permissions:
                permissions_dict = page_permissions_for_role(levels=role_to_update.level)
                role_to_update.permissions = permissions_dict  # type: ignore[assignment]
            else:
                role_to_update.permissions = update_data.permissions  # type: ignore[assignment]

            # Whenever permissions change, automatically sync default_features
            # so that modules like "Dashboard" reflect whether any underlying
            # actions are enabled.
            role_to_update.default_features = self._sync_default_features_from_permissions(
                role_to_update.permissions or {}
            )  # type: ignore[assignment]

            del update_dict["permissions"]

        for key, value in update_dict.items():
            setattr(role_to_update, key, value)

        # Persist role changes
        await self.db.commit()
        await self.db.refresh(role_to_update)

        # After the role's default_features are updated, sync all users that have this role
        # so their feature_toggles mirror the new defaults.
        await self.db.execute(
            update(User)
            .where(User.role_id == role_to_update.id)
            .values(feature_toggles=role_to_update.default_features or {})
        )
        await self.db.commit()

        return role_to_update

    async def delete_role(self, role_id: int, deleter: User) -> bool:
        role_to_delete = await self.get_role_by_id(role_id)
        if not role_to_delete:
            return False
        
        if not deleter.role.level > role_to_delete.level:
            raise RoleHierarchyError("You cannot delete a role with a level equal to or higher than your own.")

        if bool(role_to_delete.is_default):
            raise InsufficientPermissionsError("Default system roles cannot be deleted.")

        # Count only active users with this role
        active_user_count_query = select(func.count(User.id)).where(
            User.role_id == role_id,
            User.is_active == True
        )
        active_user_count = (await self.db.execute(active_user_count_query)).scalar_one()
        
        if active_user_count > 0:
            raise ValueError(f"Cannot delete role '{role_to_delete.name}' as it is currently assigned to {active_user_count} active user(s).")

        # If there are inactive users with this role, delete them before deleting the role
        # Use noload to prevent loading menu_items relationships that reference non-existent columns
        from sqlalchemy.orm import noload
        inactive_users_query = (
            select(User)
            .options(
                noload(User.created_menu_items),
                noload(User.updated_menu_items),
                noload(User.created_counters),
                noload(User.updated_counters),
                noload(User.created_categories),
                noload(User.updated_categories)
            )
            .where(
                User.role_id == role_id,
                User.is_active == False
            )
        )
        inactive_users_result = await self.db.execute(inactive_users_query)
        inactive_users = inactive_users_result.scalars().all()
        
        if inactive_users:
            # Before deleting inactive users, clear any counter staff assignments
            # that reference them to avoid foreign key violations on counters.staff_assign_id.
            user_ids = [u.id for u in inactive_users if u.id is not None]
            if user_ids:
                await self.db.execute(
                    update(Counter)
                    .where(Counter.staff_assign_id.in_(user_ids))
                    .values(staff_assign_id=None)
                )
                await self.db.flush()

            # Delete all inactive users with this role
            for user in inactive_users:
                await self.db.delete(user)
            await self.db.flush()  # Flush before deleting the role

        # Now delete the role
        await self.db.delete(role_to_delete)
        await self.db.commit()
        return True