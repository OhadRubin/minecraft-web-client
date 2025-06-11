import React, { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import ImageGallery from 'react-image-gallery';
import 'react-image-gallery/styles/css/image-gallery.css';

interface StoredScreenshot {
    image: string;
    timestamp: number;
    width: number;
    height: number;
    botStatus?: any;
}

interface ScreenshotGalleryProps {
    screenshots?: StoredScreenshot[];
    maxScreenshots?: number;
}

const ScreenshotGallery: React.FC<ScreenshotGalleryProps> = ({ 
    screenshots = [], 
    maxScreenshots = 20 
}) => {
    const [screenshotList, setScreenshotList] = useState<StoredScreenshot[]>(screenshots);
    const [currentIndex, setCurrentIndex] = useState(0);

    // Format timestamp for display
    const formatTimestamp = (timestamp: number): string => {
        return new Date(timestamp).toLocaleTimeString();
    };

    // Update screenshots from external source
    useEffect(() => {
        (window as any).updateScreenshotGallery = (newScreenshots: StoredScreenshot[]) => {
            console.log('🎯 Gallery update received:', newScreenshots ? newScreenshots.length : 'null');
            console.log('🎯 Update data:', newScreenshots);
            if (Array.isArray(newScreenshots)) {
                console.log('🎯 Setting screenshot list with', newScreenshots.length, 'items');
                setScreenshotList(newScreenshots.slice(0, maxScreenshots));
                if (newScreenshots.length > 0) {
                    setCurrentIndex(0);
                }
            } else {
                console.warn('🎯 newScreenshots is not an array:', typeof newScreenshots);
            }
        };

        return () => {
            delete (window as any).updateScreenshotGallery;
        };
    }, [maxScreenshots]);

    // Convert screenshots to gallery format
    const galleryItems = screenshotList.map((screenshot, index) => {
        const dataUrl = `data:image/png;base64,${screenshot.image}`;
        return {
            original: dataUrl,
            thumbnail: dataUrl,
            description: `Screenshot ${index + 1} - ${formatTimestamp(screenshot.timestamp)}`
        };
    });

    // Empty state
    if (screenshotList.length === 0) {
        return (
            <div className="screenshot-gallery-empty" style={{
                height: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
            }}>
                <div style={{ textAlign: 'center', color: '#666' }}>
                    <div style={{ fontSize: '48px', marginBottom: '15px' }}>📸</div>
                    <h3 style={{ margin: '0 0 10px 0', color: '#333' }}>No Screenshots Yet</h3>
                    <p style={{ margin: '0 0 15px 0', color: '#777' }}>
                        Screenshots will appear here when captured from Minecraft
                    </p>
                    <div style={{ fontSize: '12px', color: '#999' }}>
                        <div>✅ WebSocket integration ready</div>
                        <div>✅ React Image Gallery loaded</div>
                        <div>✅ Metadata display configured</div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="screenshot-gallery" style={{ height: '100%' }}>
            <ImageGallery
                items={galleryItems}
                currentIndex={currentIndex}
                onSlide={setCurrentIndex}
                showThumbnails={true}
                showFullscreenButton={true}
                showPlayButton={false}
                showNav={true}
                renderItem={(item) => (
                    <div className="image-gallery-image">
                        <img 
                            src={item.original} 
                            alt={item.description}
                            style={{ maxWidth: '100%', maxHeight: '400px', objectFit: 'contain' }}
                        />
                        <div style={{
                            backgroundColor: 'rgba(0,0,0,0.8)',
                            color: 'white',
                            padding: '10px',
                            fontSize: '12px',
                            marginTop: '5px'
                        }}>
                            {item.description}
                        </div>
                    </div>
                )}
            />
            <div style={{
                textAlign: 'center',
                padding: '5px',
                fontSize: '12px',
                color: '#666',
                backgroundColor: '#f8f9fa',
                borderTop: '1px solid #ddd'
            }}>
                {screenshotList.length > 0 && (
                    <span>
                        {currentIndex + 1} of {screenshotList.length} screenshots
                    </span>
                )}
            </div>
        </div>
    );
};

// Mount function for external use
export function mountScreenshotGallery(container: HTMLElement) {
    const root = createRoot(container);
    root.render(React.createElement(ScreenshotGallery, {}));
    return root;
}

export default ScreenshotGallery;