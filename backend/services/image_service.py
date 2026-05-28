"""Image upload service using Cloudinary"""
import base64
from backend.config import Config
import cloudinary
import cloudinary.uploader

# Configure Cloudinary
cloudinary.config(
    cloud_name=Config.CLOUDINARY_CLOUD_NAME,
    api_key=Config.CLOUDINARY_API_KEY,
    api_secret=Config.CLOUDINARY_API_SECRET
)

class ImageService:
    @staticmethod
    def upload_image(file_data, folder='products'):
        """Upload image to Cloudinary."""
        if not Config.CLOUDINARY_CLOUD_NAME or not Config.CLOUDINARY_API_KEY or not Config.CLOUDINARY_API_SECRET:
            raise RuntimeError('Cloudinary configuration is required for image uploads')

        try:
            result = cloudinary.uploader.upload(
                file_data,
                folder=folder,
                transformation=[
                    {'width': 1200, 'height': 1200, 'crop': 'limit'},
                    {'quality': 'auto:good'},
                    {'fetch_format': 'auto'}
                ]
            )

            thumbnail_url = cloudinary.CloudinaryImage(result['public_id']).build_url(
                width=300,
                height=300,
                crop='fill',
                quality='auto:good'
            )

            return {
                'url': result['secure_url'],
                'thumbnail_url': thumbnail_url,
                'public_id': result['public_id']
            }

        except Exception as e:
            raise RuntimeError(f'Cloudinary upload failed: {e}') from e

    @staticmethod
    def delete_image(public_id):
        """Delete image from Cloudinary."""
        if not Config.CLOUDINARY_CLOUD_NAME:
            return

        try:
            cloudinary.uploader.destroy(public_id)
        except Exception as e:
            raise RuntimeError(f'Cloudinary deletion failed: {e}') from e
