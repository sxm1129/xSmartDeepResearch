import React from 'react';
import { Icon } from './Icon';

interface ErrorModalProps {
  onClose: () => void;
}

export const ErrorModal: React.FC<ErrorModalProps> = ({ onClose }) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
        <div className="relative w-full max-w-2xl bg-white rounded-xl shadow-2xl border border-slate-200 flex flex-col max-h-[90vh] overflow-hidden">
            {/* Header */}
            <div className="flex items-start justify-between p-6 border-b border-slate-100">
                <div className="flex gap-4">
                    <div className="flex-shrink-0 w-12 h-12 rounded-full bg-red-50 flex items-center justify-center text-red-600">
                        <Icon name="warning" className="text-[28px]" fill />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold text-slate-900 leading-tight">Connection Diagnostics</h2>
                        <p className="mt-1 text-sm text-slate-500">Connection attempt to OpenAI API failed.</p>
                    </div>
                </div>
                <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition-colors">
                    <Icon name="close" />
                </button>
            </div>

            {/* Content */}
            <div className="overflow-y-auto p-6 flex-1">
                <div className="mb-6">
                    <div className="flex items-center justify-between mb-2">
                        <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                            <Icon name="terminal" className="text-lg text-slate-400" />
                            Server Response
                        </h3>
                        <span className="text-xs font-medium px-2 py-0.5 rounded bg-red-100 text-red-700 border border-red-200">Error 401</span>
                    </div>
                    <div className="relative group">
                         <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                            <button className="bg-white hover:bg-gray-50 text-slate-700 text-xs font-medium py-1.5 px-3 rounded shadow-sm border border-gray-200 flex items-center gap-1.5">
                                <Icon name="content_copy" className="text-[16px]" /> Copy
                            </button>
                        </div>
                        <pre className="w-full bg-[#1e1e1e] text-gray-300 font-mono text-sm rounded-lg p-4 overflow-x-auto border border-gray-800 shadow-inner">
<code>{`{
  "error": {
    "message": "Incorrect API key provided: sk-proj-********************. You can find your API key at https://platform.openai.com/account/api-keys.",
    "type": "invalid_request_error",
    "param": null,
    "code": 401
  }
}`}</code>
                        </pre>
                    </div>
                </div>

                <div className="bg-blue-50/50 rounded-lg p-5 border border-blue-100">
                    <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
                        <Icon name="build_circle" className="text-primary text-lg" />
                        Suggested Fixes
                    </h3>
                    <ul className="space-y-3">
                        <li className="flex items-start gap-3 text-sm text-slate-600">
                            <Icon name="check_circle" className="text-green-600 text-lg mt-0.5 shrink-0" fill />
                            <span>Verify that your API key is active and correctly pasted in the project settings.</span>
                        </li>
                        <li className="flex items-start gap-3 text-sm text-slate-600">
                            <Icon name="radio_button_unchecked" className="text-slate-400 text-lg mt-0.5 shrink-0" />
                            <span>Check your network proxy settings if you are behind a corporate firewall.</span>
                        </li>
                        <li className="flex items-start gap-3 text-sm text-slate-600">
                             <Icon name="radio_button_unchecked" className="text-slate-400 text-lg mt-0.5 shrink-0" />
                             <span>Ensure your account billing quota has not been exceeded on the provider dashboard.</span>
                        </li>
                    </ul>
                </div>
            </div>

            {/* Footer */}
            <div className="p-6 border-t border-slate-100 bg-slate-50 rounded-b-xl flex justify-end gap-3">
                <button onClick={onClose} className="px-5 py-2.5 rounded-lg text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-200 transition-colors">
                    Close
                </button>
                <button className="px-5 py-2.5 rounded-lg text-sm font-medium text-white bg-primary hover:bg-primary-dark shadow-sm flex items-center gap-2 transition-all active:scale-95">
                    <Icon name="refresh" className="text-[18px]" />
                    Retry Connection
                </button>
            </div>
        </div>
    </div>
  );
};