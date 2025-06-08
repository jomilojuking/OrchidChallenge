'use client';

import { useState } from 'react';

interface CloneResponse {
  success: boolean;
  generated_html: string;
  original_url: string;
}

export default function Home() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<CloneResponse | null>(null);
  const [error, setError] = useState('');
  const [progress, setProgress] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    setLoading(true);
    setError('');
    setResult(null);
    setProgress('Initializing...');

    try {
      // Simulate progress updates
      const progressSteps = [
        'Connecting to website...',
        'Capturing screenshots...',
        'Analyzing page structure...',
        'Extracting design elements...',
        'Generating clone with AI...',
        'Finalizing HTML...'
      ];

      let stepIndex = 0;
      const progressInterval = setInterval(() => {
        if (stepIndex < progressSteps.length) {
          setProgress(progressSteps[stepIndex]);
          stepIndex++;
        }
      }, 2000);

      const response = await fetch('http://localhost:8000/clone', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url }),
      });

      clearInterval(progressInterval);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: CloneResponse = await response.json();
      setResult(data);
      setProgress('Complete!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setProgress('');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-500 p-8 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-white/10 rounded-full blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-white/10 rounded-full blur-3xl"></div>
      </div>

      <main className="max-w-6xl mx-auto text-center relative z-10">
        <div className="mb-12">
          <h1 className="text-7xl font-bold text-white mb-6 tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-blue-100">
            Orchid Challenge
          </h1>
          <p className="text-2xl text-white/90 mb-3 font-light">
            AI-powered website cloning with pixel-perfect accuracy
          </p>
          <p className="text-white/70 text-base">
            Enter any website URL to create a complete HTML replica
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mb-12">
          <div className="flex flex-col gap-4 max-w-xl mx-auto">
            <div className="relative group">
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://example.com"
                className="w-full px-6 py-5 text-lg rounded-2xl border-0 outline-none text-gray-800 shadow-xl focus:ring-4 focus:ring-white/30 transition-all bg-white/95 backdrop-blur-sm"
                disabled={loading}
                required
              />
              <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-blue-500/20 to-purple-500/20 opacity-0 group-hover:opacity-100 transition-opacity -z-10 blur-xl"></div>
            </div>
            <button 
              type="submit" 
              className={`px-8 py-5 text-lg rounded-2xl font-medium transition-all transform ${
                loading || !url.trim() 
                  ? 'bg-gray-400/50 cursor-not-allowed scale-95' 
                  : 'bg-white hover:bg-white/90 hover:scale-[1.02] shadow-xl hover:shadow-2xl cursor-pointer'
              } text-gray-900 relative group overflow-hidden`}
              disabled={loading || !url.trim()}
            >
              <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 to-purple-500/20 opacity-0 group-hover:opacity-100 transition-opacity"></div>
              {loading ? (
                <div className="flex items-center justify-center gap-3 relative">
                  <div className="w-5 h-5 border-2 border-gray-900 border-t-transparent rounded-full animate-spin"></div>
                  <span className="relative">Cloning Website...</span>
                </div>
              ) : (
                <span className="relative">Clone Website</span>
              )}
            </button>
          </div>
        </form>

        {progress && loading && (
          <div className="mb-8 max-w-xl mx-auto">
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20">
              <div className="text-white font-medium mb-3 text-lg">{progress}</div>
              <div className="w-full bg-white/20 rounded-full h-2.5 overflow-hidden">
                <div 
                  className="bg-gradient-to-r from-blue-400 to-purple-400 h-full rounded-full transition-all duration-500 ease-out"
                  style={{width: '60%'}}
                ></div>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-500/10 backdrop-blur-md border border-red-500/20 text-red-100 px-6 py-4 rounded-2xl mb-8 max-w-xl mx-auto shadow-xl">
            <strong className="text-red-200">Error:</strong> {error}
          </div>
        )}

        {result && (
          <div className="bg-white/10 backdrop-blur-xl rounded-3xl shadow-2xl p-8 text-left border border-white/20">
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-3xl font-bold text-white">Clone Results</h2>
              <div className="bg-green-500/20 text-green-100 px-4 py-2 rounded-full text-sm font-medium border border-green-500/20">
                ✅ Successfully Cloned
              </div>
            </div>
            
            <div className="space-y-8">
              <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10">
                <h3 className="text-lg font-medium mb-3 text-white/90 flex items-center">
                  <span className="w-2 h-2 bg-blue-400 rounded-full mr-3"></span>
                  Original Website
                </h3>
                <a 
                  href={result.original_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-blue-300 hover:text-blue-100 break-all text-sm underline transition-colors"
                >
                  {result.original_url}
                </a>
              </div>
              
              <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-lg font-medium text-white/90 flex items-center">
                    <span className="w-2 h-2 bg-green-400 rounded-full mr-3"></span>
                    Generated Clone
                  </h3>
                  <button
                    onClick={() => {
                      const blob = new Blob([result.generated_html], { type: 'text/html' });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = 'cloned-website.html';
                      a.click();
                      URL.revokeObjectURL(url);
                    }}
                    className="bg-white/10 hover:bg-white/20 text-white px-4 py-2 rounded-xl text-sm font-medium transition-all border border-white/20 hover:border-white/30"
                  >
                    Download HTML
                  </button>
                </div>
                
                <div className="border border-white/20 rounded-xl overflow-hidden">
                  <div className="bg-white/10 px-4 py-2 border-b border-white/20">
                    <span className="text-white/70 text-sm font-medium">Live Preview</span>
                  </div>
                  <div className="bg-white" style={{ height: '600px', overflow: 'auto' }}>
                    <iframe
                      srcDoc={result.generated_html}
                      className="w-full h-full border-0"
                      title="Cloned Website Preview"
                      sandbox="allow-same-origin allow-scripts"
                    />
                  </div>
                </div>
                
                <div className="mt-4">
                  <details className="group">
                    <summary className="cursor-pointer text-white/70 hover:text-white font-medium transition-colors">
                      View HTML Source Code
                    </summary>
                    <div className="mt-3 bg-gray-900/50 text-green-400 p-4 rounded-xl overflow-auto max-h-60 text-xs border border-white/10">
                      <pre>{result.generated_html}</pre>
                    </div>
                  </details>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}