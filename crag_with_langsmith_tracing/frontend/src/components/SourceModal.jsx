import React from "react";
import { X } from "lucide-react";

export const SourceModal = ({ isOpen, onClose, sourceContent }) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Document Source Content</h3>
          <button className="close-modal-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>
        <div className="modal-body">
          {sourceContent}
        </div>
      </div>
    </div>
  );
};
