from pydantic import BaseModel, Field

class UserAssignBranch(BaseModel):
    """Schema for assigning a user to a branch."""
    branch_id: int = Field(..., gt=0, description="The sequence ID of the branch to assign the user to.")