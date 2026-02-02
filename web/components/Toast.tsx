import React, { useEffect } from 'react';
import { Icon } from './Icon';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface ToastProps {
    id: string;
    message: string;
    type: ToastType;
    duration?: number;
    onClose: (id: string) => void;
}

export const Toast: React.FC<ToastProps> = ({ id, message, type, duration = 3000, onClose }) => {
    useEffect(() => {
        const timer = setTimeout(() => {
            onClose(id);
        }, duration);
        return () => clearTimeout(timer);
    }, [id, duration, onClose]);

    const bgColors = {
        success: 'bg-emerald-50 border-emerald-200 text-emerald-800',
        error: 'bg-red-50 border-red-200 text-red-800',
        info: 'bg-blue-50 border-blue-200 text-blue-800',
        warning: 'bg-amber-50 border-amber-200 text-amber-800'
    };

    const icons = {
        success: 'check_circle',
        error: 'error',
        info: 'info',
        warning: 'warning'
    };

    return (
        <div className={`pointer-events-auto flex items-center w-full max-w-sm p-4 mb-4 rounded-lg shadow-lg border ${bgColors[type]} animate-in slide-in-from-right-full duration-300`}>
            <div className="flex-shrink-0">
                <Icon name={icons[type]} className="w-5 h-5" />
            </div>
            <div className="ml-3 text-sm font-medium">{message}</div>
            <button
                onClick={() => onClose(id)}
                className="ml-auto -mx-1.5 -my-1.5 rounded-lg p-1.5 inline-flex h-8 w-8 hover:bg-black/5"
            >
                <Icon name="close" className="w-4 h-4" />
            </button>
        </div>
    );
};
