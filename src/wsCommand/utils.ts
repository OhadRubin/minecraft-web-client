import * as THREE from 'three'

/**
 * Resizes a base64 image to specified width while maintaining aspect ratio
 * @param {string} base64String - The base64 encoded image string (with or without data URL prefix)
 * @param {number} targetWidth - Target width in pixels (default: 1080)
 * @returns {Promise<string>} - Promise that resolves to the resized image as base64 string
 */
export function resizeImageBase64(base64String: string, targetWidth: number = 1080): Promise<string> {
  return new Promise((resolve, reject) => {
    // Create an image element
    const img = new Image();

    // Handle image load
    img.onload = function () {
      // Calculate the new dimensions maintaining aspect ratio
      const originalWidth = img.width;
      const originalHeight = img.height;
      const aspectRatio = originalHeight / originalWidth;

      const newWidth = targetWidth;
      const newHeight = Math.round(newWidth * aspectRatio);

      // Create a canvas element
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');

      if (!ctx) {
        reject(new Error('Failed to get canvas context'));
        return;
      }

      // Set canvas dimensions
      canvas.width = newWidth;
      canvas.height = newHeight;

      // Draw the resized image on canvas
      ctx.drawImage(img, 0, 0, newWidth, newHeight);

      // Convert canvas to base64
      const resizedBase64 = canvas.toDataURL('image/jpeg', 0.9);

      resolve(resizedBase64);
    };

    // Handle image load error
    img.onerror = function () {
      reject(new Error('Failed to load image from base64 string'));
    };

    // Set the image source
    // Handle both cases: with and without data URL prefix
    if (base64String.startsWith('data:')) {
      img.src = base64String;
    } else {
      img.src = `data:image/jpeg;base64,${base64String}`;
    }
  });
}

export function createTextSprite(text: string): THREE.Sprite {
  const canvas = document.createElement('canvas')
  const context = canvas.getContext('2d')!
  const fontSize = 20
  context.font = `${fontSize}px Arial`
  const textWidth = context.measureText(text).width + 4
  canvas.width = textWidth
  canvas.height = fontSize * 1.5
  context.font = `${fontSize}px Arial`
  context.fillStyle = 'white'
  context.strokeStyle = 'black'
  context.lineWidth = 4
  context.strokeText(text, 2, fontSize)
  context.fillText(text, 2, fontSize)
  const texture = new THREE.CanvasTexture(canvas)
  const material = new THREE.SpriteMaterial({ map: texture, transparent: true })
  const sprite = new THREE.Sprite(material)
  sprite.scale.set(canvas.width / 20, canvas.height / 20, 1)
  return sprite
}