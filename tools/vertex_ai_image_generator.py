#!/usr/bin/env python3
"""
Simple MCP Server for Google Cloud Vertex AI Image Generation
Optimized to avoid generating Python scaffolding each time
"""

import asyncio
import json
import base64
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    from google.cloud import aiplatform
    from vertexai.preview.vision_models import ImageGenerationModel
    import vertexai
    from google.auth import default
except ImportError:
    print("Error: google-cloud-aiplatform not installed")
    print("Install with: pip install google-cloud-aiplatform")
    sys.exit(1)


class VertexAIImageGenerator:
    def __init__(self):
        self.project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
        self.location = os.environ.get('GOOGLE_CLOUD_REGION', 'us-central1')
        self.model_name = os.environ.get('GOOGLE_IMAGE_MODEL', 'imagegeneration@006')

        # Set up authentication credentials path if provided
        credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if credentials_path and os.path.exists(credentials_path):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.abspath(credentials_path)

        if not self.project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable required")

        # Initialize Vertex AI
        vertexai.init(project=self.project_id, location=self.location)

    def generate_image(self, prompt: str, aspect_ratio: str = "16:9", output_dir: str = None):
        """Generate image using Vertex AI Imagen"""

        try:
            # Use the model directly without endpoint discovery
            from vertexai.preview.vision_models import ImageGenerationModel

            # Initialize the image generation model
            model = ImageGenerationModel.from_pretrained(self.model_name)

            # Generate image using the direct model approach
            response = model.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio=aspect_ratio,
                safety_filter_level="block_some",
                person_generation="allow_adult"
            )

            if not response or not response.images:
                return {
                    "success": False,
                    "error": "No images returned from Vertex AI"
                }

            # Get the first generated image
            image = response.images[0]

            # Get image data as bytes
            image_data = image._image_bytes

            # Save image if output directory specified
            saved_path = None
            if output_dir:
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)

                # Create filename based on prompt
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_prompt = "".join(c for c in prompt[:30] if c.isalnum() or c in (' ', '-', '_')).rstrip()
                safe_prompt = safe_prompt.replace(' ', '_')
                filename = f"imagen_{timestamp}_{safe_prompt}.jpg"

                # Save image bytes directly
                saved_path = output_path / filename

                with open(saved_path, 'wb') as f:
                    f.write(image_data)

            return {
                "success": True,
                "prompt": prompt,
                "saved_path": str(saved_path) if saved_path else None,
                "file_size": len(image_data) if image_data else 0,
                "model": self.model_name
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Generation failed: {str(e)}"
            }


def main():
    """Command line interface for the Vertex AI image generator"""
    import argparse

    parser = argparse.ArgumentParser(description="Generate images using Google Cloud Vertex AI")
    parser.add_argument("prompt", help="Image generation prompt")
    parser.add_argument("--aspect-ratio", default="16:9", help="Image aspect ratio (default: 16:9)")
    parser.add_argument("--output-dir", help="Directory to save generated image")

    args = parser.parse_args()

    generator = VertexAIImageGenerator()
    result = generator.generate_image(
        prompt=args.prompt,
        aspect_ratio=args.aspect_ratio,
        output_dir=args.output_dir
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()