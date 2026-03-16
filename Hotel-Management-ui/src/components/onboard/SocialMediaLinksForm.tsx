'use client';
import React from 'react';
import { useRouter } from 'next/navigation';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';
import SuccessPopup from '@/components/popup/SuccessPopup';
import { useTheme } from '@/contexts/ThemeContext';
import { OnboardingPayload, OnboardingResponse } from '@/types/onboarding';
import { onboardingService } from '@/api/onboarding'; 
import popupimg from '@/assests/onboardingpopimg.svg'
import { SocialMediaLinksData } from '@/types/onboarding'

interface SocialMediaLinksFormProps {
  onBack: () => void;
  aggregated?: Partial<OnboardingPayload>;
  onSuccess?: (response: OnboardingResponse, payload: OnboardingPayload) => void;
}


const SocialMediaLinksForm: React.FC<SocialMediaLinksFormProps> = ({
  onBack,
  aggregated,
}) => {
  const { theme } = useTheme();
  const router = useRouter();
  const [formData, setFormData] = React.useState<SocialMediaLinksData>({
    googleReviewLink: '',
    youtubeLink: '',
    instagramLink: '',
    xLink: '',
    facebookLink: '',
    website: '',
  });

  const [errors, setErrors] = React.useState<Partial<SocialMediaLinksData>>({});
  const [snackbar, setSnackbar] = React.useState<{ open: boolean; message: string }>({ open: false, message: '' });
  const [showSuccess, setShowSuccess] = React.useState<boolean>(false);
  const [loading, setLoading] = React.useState(false);

  const handleChange = (field: keyof SocialMediaLinksData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setErrors((prev) => ({ ...prev, [field]: '' }));
  };

  const validate = () => {
    const newErrors: Partial<SocialMediaLinksData> = {};
    // Basic URL validation (can be enhanced)
    const urlRegex = /^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$/;

    if (formData.googleReviewLink && !urlRegex.test(formData.googleReviewLink)) {
      newErrors.googleReviewLink = 'Invalid URL';
    }
    if (formData.youtubeLink && !urlRegex.test(formData.youtubeLink)) {
      newErrors.youtubeLink = 'Invalid URL';
    }
    if (formData.instagramLink && !urlRegex.test(formData.instagramLink)) {
      newErrors.instagramLink = 'Invalid URL';
    }
    if (formData.xLink && !urlRegex.test(formData.xLink)) {
      newErrors.xLink = 'Invalid URL';
    }
    if (formData.facebookLink && !urlRegex.test(formData.facebookLink)) {
      newErrors.facebookLink = 'Invalid URL';
    }
    if (formData.website && !urlRegex.test(formData.website)) {
      newErrors.website = 'Invalid URL';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();

    if (!validate()) return;

    setLoading(true);
    try {
      const payload: OnboardingPayload = {
        hotel_name: aggregated?.hotel_name ?? '',
        owner_name: aggregated?.owner_name ?? '',
        gst_number: aggregated?.gst_number ?? '',
        business_type: aggregated?.business_type ?? '',
        logo_url: aggregated?.logo_url ?? '',
        logo: aggregated?.logo ?? null,
        description: aggregated?.description ?? '',
        address_line_1: aggregated?.address_line_1 ?? '',
        address_line_2: aggregated?.address_line_2 ?? '',
        area: aggregated?.area ?? '',
        city: aggregated?.city ?? '',
        pincode: aggregated?.pincode ?? '',
        state: aggregated?.state ?? '',
        fssai_number: aggregated?.fssai_number ?? '',
        tin_number: aggregated?.tin_number ?? '',
        professional_tax_reg_number: aggregated?.professional_tax_reg_number ?? '',
        trade_license_number: aggregated?.trade_license_number ?? '',
        bank_details: aggregated?.bank_details ?? {},
        social_media_links: {
          google_review_link: formData.googleReviewLink,
          youtube_link: formData.youtubeLink,
          instagram_link: formData.instagramLink,
          x_link: formData.xLink,
          facebook_link: formData.facebookLink,
          website: formData.website,
          ...(aggregated?.social_media_links || {}),
        },
      };

      const res = await onboardingService.submit(payload);
      console.log('Onboarding response:', res);
      if (res.success) {
        setShowSuccess(true);
      } else {
        setSnackbar({ open: true, message: res.errors?.general || res.message || 'Onboarding failed.' });
        setTimeout(() => setSnackbar({ open: false, message: '' }), 4000);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-md p-8 w-full max-w-6xl mx-auto">
      {showSuccess && (
        <SuccessPopup
          title="All Set!"
          successImage={popupimg}
          subtitle="Your onboarding is complete. Everything is ready for you to start managing operations"
          BtnName="Go Dashboard"
          onClose={() => setShowSuccess(false)}
          onConfirm={() => router.push('/dashboard')}
        />
      )}
      {snackbar.open && (
        <div
          style={{
            position: 'fixed',
            bottom: 32,
            left: '50%',
            transform: 'translateX(-50%)',
            background: '#EF4444',
            color: '#fff',
            padding: '14px 32px',
            borderRadius: '8px',
            fontWeight: 500,
            fontSize: '16px',
            boxShadow: '0 2px 12px rgba(0,0,0,0.15)',
            zIndex: 9999,
          }}
        >
          {snackbar.message}
        </div>
      )}
      <h2 className="text-xl font-bold mb-1" style={{ color: theme.text }}>
        Social Media Links
      </h2>
      <p className="text-gray-500 mb-6">
        Enter your hotels official social media pages to improve visibility and trust.
      </p>

      <div className="grid grid-cols-2 gap-6">
        <Input
          label="Google review link"
          placeholder="eg. https://g.page/r/Cf93kfj34x2bE"
          value={formData.googleReviewLink}
          tooltip='100%'
          errori='90%'
          error={errors.googleReviewLink}
          onChange={(e) => handleChange('googleReviewLink', e.target.value)}
        />
        <Input
          label="YouTube link"
          placeholder="eg. https://youtube.com/yourhotel"
          value={formData.youtubeLink}
          tooltip='100%'
          errori='90%'
          error={errors.youtubeLink}
          onChange={(e) => handleChange('youtubeLink', e.target.value)}
        />
        <Input
          label="Instagram Link"
          placeholder="eg. https://instagram.com/yourhotel"
          value={formData.instagramLink}
          tooltip='100%'
          errori='90%'
          error={errors.instagramLink}
          onChange={(e) => handleChange('instagramLink', e.target.value)}
        />
        <Input
          label="X Link"
          placeholder="eg. https://x.com/yourhotel"
          value={formData.xLink}
          tooltip='100%'
          errori='90%'
          error={errors.xLink}
          onChange={(e) => handleChange('xLink', e.target.value)}
        />
        <Input
          label="Facebook Link"
          placeholder="eg. https://facebook.com/yourhotel"
          value={formData.facebookLink}
          tooltip='100%'
          errori='90%'
          error={errors.facebookLink}
          onChange={(e) => handleChange('facebookLink', e.target.value)}
        />
        <Input
          label="Website"
          placeholder="eg. https://www.yourhotel.com"
          value={formData.website}
          tooltip='100%'
          errori='90%'
          error={errors.website}
          onChange={(e) => handleChange('website', e.target.value)}
        />
      </div>

      <div className="flex justify-end gap-5 mt-8">
        <Button
          className='w-[151px] h-[42px]'
          variant="text"
          onClick={onBack}
          sx={{ bgcolor: 'var(--Light, #E0F3E2)', color: theme.secondary, borderRadius: '8px', px: 4, py: 1, height: '42px', width: '151px' }}
        >
          Back
        </Button>
        <Button
          className='w-[151px] h-[42px]'
          variant="contained"
          onClick={handleSubmit}
          sx={{
            backgroundColor: theme.primary,
            borderRadius: '8px',
            px: 4,
            py: 1,
            height: '42px', width: '151px'
          }}
          loading={loading}
        >
          Submit
        </Button>
      </div>
    </div>
  );
};

export default SocialMediaLinksForm;
