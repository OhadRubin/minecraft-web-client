import React, { useState, useEffect, useCallback } from 'react';
import ImageGallery from 'react-image-gallery';
import { StoredScreenshot } from './types.js';

interface ImageGalleryItem {
    original: string;
    thumbnail: string;
    description: string;
    originalTitle: string;
}

interface ScreenshotGalleryProps {
    screenshots?: StoredScreenshot[];
    maxScreenshots?: number;
}

const ScreenshotGallery: React.FC<ScreenshotGalleryProps> = ({ 
    screenshots: initialScreenshots = [], 
    maxScreenshots = 20 
}) => {
    const [screenshots, setScreenshots] = useState<StoredScreenshot[]>(initialScreenshots);
    const [currentIndex, setCurrentIndex] = useState(0);

    // Format timestamp for display
    const formatTimestamp = useCallback((timestamp: number): string => {
        return new Date(timestamp).toLocaleTimeString();
    }, []);

    // Format bot position for display
    const formatPosition = useCallback((position: [number, number, number]): string => {
        const [x, y, z] = position;
        return `(${x.toFixed(1)}, ${y.toFixed(1)}, ${z.toFixed(1)})`;
    }, []);

    // Generate event description based on screenshot context
    const generateEventDescription = useCallback((screenshot: StoredScreenshot, index: number): string => {
        const timestamp = formatTimestamp(screenshot.timestamp);
        const position = screenshot.botStatus ? formatPosition(screenshot.botStatus.position) : 'Unknown';
        
        // Create descriptive text based on screenshot metadata
        let eventType = 'Screenshot Captured';
        if (screenshot.botStatus?.lookingAt) {
            eventType = `Viewing ${screenshot.botStatus.lookingAt.name}`;
        }
        
        return `${timestamp} - ${eventType} - Position ${position}`;
    }, [formatTimestamp, formatPosition]);

    // Convert screenshots to ImageGallery format
    const galleryItems: ImageGalleryItem[] = screenshots.map((screenshot, index) => {
        const dataUrl = `data:image/png;base64,${screenshot.image}`;
        const description = generateEventDescription(screenshot, index);
        
        return {
            original: dataUrl,
            thumbnail: dataUrl,
            description: description,
            originalTitle: description
        };
    });

    // Handle screenshot updates from WebSocket
    const updateScreenshots = useCallback((newScreenshots: StoredScreenshot[]) => {
        setScreenshots(newScreenshots.slice(0, maxScreenshots));
        // Reset to first image when new screenshots arrive
        if (newScreenshots.length > 0) {
            setCurrentIndex(0);
        }
    }, [maxScreenshots]);

    // Global function to update gallery from WebSocket
    useEffect(() => {
        const updateGallery = (data: any) => {
            console.log('Gallery update received:', data);
            
            // Check if this is a screenshot update
            if (data && Array.isArray(data)) {
                updateScreenshots(data);
            } else if (typeof data === 'string' && data.includes('screenshot')) {
                // Handle legacy string-based updates
                console.log('Legacy screenshot update:', data);
            }
        };

        // Make the update function globally available
        (window as any).updateScreenshotGallery = updateGallery;

        // Cleanup
        return () => {
            if ((window as any).updateScreenshotGallery === updateGallery) {
                delete (window as any).updateScreenshotGallery;
            }
        };
    }, [updateScreenshots]);

    // Handle slide change
    const handleSlideChange = useCallback((index: number) => {
        setCurrentIndex(index);
    }, []);

    // Render thumbnail with metadata overlay
    const renderThumbInner = useCallback((item: ImageGalleryItem) => {
        const screenshot = screenshots[galleryItems.indexOf(item)];
        if (!screenshot) return null;

        return (
            <div className="image-gallery-thumbnail-inner">
                <img 
                    src={item.thumbnail} 
                    alt={item.description}
                    style={{ width: '100%', height: '60px', objectFit: 'cover' }}
                />
                <div className="thumbnail-metadata">
                    <div className="thumbnail-time">
                        {formatTimestamp(screenshot.timestamp)}
                    </div>
                    {screenshot.botStatus && (
                        <div className="thumbnail-position">
                            {formatPosition(screenshot.botStatus.position)}
                        </div>
                    )}
                </div>
            </div>
        );
    }, [screenshots, galleryItems, formatTimestamp, formatPosition]);

    // Render main image with detailed metadata
    const renderItem = useCallback((item: ImageGalleryItem) => {
        const screenshot = screenshots[galleryItems.indexOf(item)];
        if (!screenshot) return null;

        return (
            <div className="image-gallery-image">
                <img 
                    src={item.original} 
                    alt={item.description}
                    style={{ maxWidth: '100%', maxHeight: '400px', objectFit: 'contain' }}
                />
                <div className="image-gallery-description">
                    <div className="screenshot-metadata">
                        <div className="metadata-row">
                            <strong>📸 {formatTimestamp(screenshot.timestamp)}</strong>
                        </div>
                        {screenshot.botStatus && (
                            <>
                                <div className="metadata-row">
                                    📍 Position: {formatPosition(screenshot.botStatus.position)}
                                </div>
                                <div className="metadata-row">
                                    👁️ View: Yaw {(screenshot.botStatus.yaw * 180 / Math.PI).toFixed(1)}°, 
                                    Pitch {(screenshot.botStatus.pitch * 180 / Math.PI).toFixed(1)}°
                                </div>
                                <div className="metadata-row">
                                    🌍 {screenshot.botStatus.biome} | 
                                    ❤️ {screenshot.botStatus.health}/20 | 
                                    🍖 {screenshot.botStatus.food}/20
                                </div>
                                {screenshot.botStatus.lookingAt && (
                                    <div className="metadata-row">
                                        👀 Looking at: {screenshot.botStatus.lookingAt.name} 
                                        ({screenshot.botStatus.lookingAt.distance.toFixed(1)} blocks)
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                </div>
            </div>
        );
    }, [screenshots, galleryItems, formatTimestamp, formatPosition]);

    // Empty state
    if (screenshots.length === 0) {
        return (
            <div className="screenshot-gallery-empty">
                <div className="empty-state">
                    <div className="empty-icon">📸</div>
                    <h3>No Screenshots Yet</h3>
                    <p>Screenshots will appear here when captured from Minecraft</p>
                    <div className="empty-features">
                        <div>✅ WebSocket integration ready</div>
                        <div>✅ React Image Gallery loaded</div>
                        <div>✅ Metadata display configured</div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="screenshot-gallery">
            <ImageGallery
                items={galleryItems}
                currentIndex={currentIndex}
                onSlide={handleSlideChange}
                showThumbnails={true}
                showFullscreenButton={false}
                showPlayButton={false}
                showBullets={false}
                showNav={true}
                thumbnailPosition="bottom"
                renderThumbInner={renderThumbInner}
                renderItem={renderItem}
            />
            <div className="gallery-status">
                {screenshots.length > 0 && (
                    <span>
                        {currentIndex + 1} of {screenshots.length} screenshots
                    </span>
                )}
            </div>
        </div>
    );
};

export default ScreenshotGallery;