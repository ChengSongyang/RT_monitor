"use client";

import { useState } from "react";
import { X, ChevronLeft, ChevronRight } from "lucide-react";

interface ImageGalleryProps {
  images: string[];
}

export function ImageGallery({ images }: ImageGalleryProps) {
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);

  if (!images || images.length === 0) return null;

  const openLightbox = (index: number) => {
    setActiveIndex(index);
    setLightboxOpen(true);
  };

  const navigate = (dir: -1 | 1) => {
    setActiveIndex((prev) => (prev + dir + images.length) % images.length);
  };

  return (
    <>
      <div className="flex gap-2 flex-wrap">
        {images.slice(0, 4).map((src, i) => (
          <button
            key={i}
            onClick={() => openLightbox(i)}
            className="group relative overflow-hidden rounded-lg border border-[var(--border)]"
          >
            <img
              src={src}
              alt={`图片 ${i + 1}`}
              className="h-20 w-20 object-cover transition-transform group-hover:scale-105"
            />
            {i === 3 && images.length > 4 && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/60 text-xs text-white">
                +{images.length - 4}
              </div>
            )}
          </button>
        ))}
      </div>

      {lightboxOpen && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80"
          onClick={() => setLightboxOpen(false)}
        >
          <button
            onClick={() => setLightboxOpen(false)}
            className="absolute right-4 top-4 text-white/80 hover:text-white"
          >
            <X className="h-6 w-6" />
          </button>

          {images.length > 1 && (
            <button
              onClick={(e) => { e.stopPropagation(); navigate(-1); }}
              className="absolute left-4 text-white/80 hover:text-white"
            >
              <ChevronLeft className="h-8 w-8" />
            </button>
          )}

          <img
            src={images[activeIndex]}
            alt={`图片 ${activeIndex + 1}`}
            className="max-h-[80vh] max-w-[80vw] rounded-lg object-contain"
            onClick={(e) => e.stopPropagation()}
          />

          {images.length > 1 && (
            <button
              onClick={(e) => { e.stopPropagation(); navigate(1); }}
              className="absolute right-4 text-white/80 hover:text-white"
            >
              <ChevronRight className="h-8 w-8" />
            </button>
          )}

          {images.length > 1 && (
            <div className="absolute bottom-4 text-sm text-white/60">
              {activeIndex + 1} / {images.length}
            </div>
          )}
        </div>
      )}
    </>
  );
}
