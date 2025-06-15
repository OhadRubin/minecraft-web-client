// Screenshot processing Web Worker
// Handles heavy image processing operations off the main thread

self.onmessage = async function(event: MessageEvent) {
  const { type, data } = event.data;
  
  if (type === 'TEST') {
    self.postMessage({
      type: 'TEST_RESPONSE',
      message: 'Worker is alive and responding!'
    });
  } else if (type === 'PROCESS_SCREENSHOT') {
    try {
      const { imageData, width, height, targetWidth } = data;
      
      // Create OffscreenCanvas for processing
      const canvas = new OffscreenCanvas(width, height);
      const ctx = canvas.getContext('2d');
      
      if (!ctx) {
        throw new Error('Failed to get OffscreenCanvas context');
      }
      
      // Put ImageData onto canvas
      ctx.putImageData(imageData, 0, 0);
      
      // Resize if needed
      let finalCanvas = canvas;
      if (targetWidth && targetWidth !== width) {
        const aspectRatio = height / width;
        const targetHeight = Math.round(targetWidth * aspectRatio);
        
        finalCanvas = new OffscreenCanvas(targetWidth, targetHeight);
        const resizeCtx = finalCanvas.getContext('2d');
        if (resizeCtx) {
          resizeCtx.drawImage(canvas, 0, 0, targetWidth, targetHeight);
        }
      }
      
      // Convert to blob and then base64
      const blob = await finalCanvas.convertToBlob({ 
        type: 'image/jpeg', 
        quality: 0.8 
      });
      
      // Convert blob to base64
      const reader = new FileReader();
      reader.onload = function() {
        const base64 = (reader.result as string).split(',')[1];
        
        self.postMessage({
          type: 'SCREENSHOT_COMPLETE',
          data: base64
        });
      };
      reader.onerror = function() {
        self.postMessage({
          type: 'SCREENSHOT_ERROR',
          error: 'FileReader failed to convert blob to base64'
        });
      };
      reader.readAsDataURL(blob);
      
    } catch (error) {
      self.postMessage({
        type: 'SCREENSHOT_ERROR',
        error: error.message
      });
    }
  }
};