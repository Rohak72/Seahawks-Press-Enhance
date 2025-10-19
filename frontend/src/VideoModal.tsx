import { useState, useEffect } from 'react';
import type { Video } from './interfaces';
import { IoClose } from 'react-icons/io5';

const API_BASE_URL = 'http://localhost:8000/api';

const formatTimestamp = (seconds: number) => {
    const date = new Date(0);
    date.setSeconds(seconds);
    const timeString = date.toISOString().substr(11, 12);
    return timeString.replace('.', ',');
};

export const VideoModal = ({ video, onClose }: { video: Video, onClose: () => void }) => {
  const [fullVideoData, setFullVideoData] = useState<Video | null>(null);

  // Use the getVideoData endpoint to pull summary and transcript details.
  useEffect(() => {
    const fetchFullVideoDetails = async () => {
      const response = await fetch(`${API_BASE_URL}/videos/getVideoData/${video.id}`);
      const data = await response.json();
      setFullVideoData(data);
    };
    fetchFullVideoDetails();
  }, [video.id]);
  
  useEffect(() => {
    const handleEsc = (event: KeyboardEvent) => { if (event.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [onClose]);

  // Helper to extract the video ID for the iframe embed.
  const getYouTubeEmbedUrl = (url: string) => {
    const videoIdMatch = url.match(/(?<=v=)[\w-]+/);
    if (!videoIdMatch) return '';
    return `https://www.youtube.com/embed/${videoIdMatch[0]}`;
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 w-full max-w-7xl h-[90vh] rounded-lg shadow-2xl flex flex-col">
        <div className="p-4 flex justify-between items-center border-b border-gray-700">
          <h2 className="text-xl font-bold truncate">{fullVideoData?.title || 'Loading...'}</h2>
          <button onClick={onClose} className="text-3xl text-gray-400 hover:text-white"><IoClose /></button>
        </div>

        {!fullVideoData ? (
          <div className="flex-grow flex items-center justify-center"><p>Loading...</p></div>
        ) : (
          <div className="flex-grow grid grid-cols-1 lg:grid-cols-3 gap-4 p-4 overflow-hidden">
            
            {/* Left column of modal has video Player + full transcript beneath. */}
            <div className="lg:col-span-2 flex flex-col h-full">
              <div className="w-full aspect-video bg-black">
                <iframe
                  src={getYouTubeEmbedUrl(fullVideoData.youtube_url)}
                  width="100%"
                  height="100%"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                  title={fullVideoData.title}
                ></iframe>
              </div>

              {/* A simple, scrollable transcript display. */}
              <div className="bg-gray-900 p-4 rounded-b-lg h-96 overflow-y-scroll">
                <h3 className="text-lg font-semibold mb-2 text-green-400">Transcript</h3>
                <div className="space-y-4">
                    {/* Here, we map over the `segments` array from our backend data. */}
                    {fullVideoData.transcript_data?.segments.map((segment, index) => (
                        <div key={index} className="flex flex-col">
                            <div className="text-xs text-gray-500 font-mono">
                                {/* Display the formatted start and end times (in grey). */}
                                <span>{formatTimestamp(segment.start)}</span>
                                <span className="mx-2">--{'>'}</span>
                                <span>{formatTimestamp(segment.end)}</span>
                            </div>
                            <p className="text-lg text-gray-200">
                                {/* Display the speaker and the text for this segment. */}
                                <span className="font-bold text-green-400 mr-2">{segment.speaker}:</span>
                                {segment.text.trim()}
                            </p>
                        </div>
                    ))}
                </div>
              </div>
            </div>

            {/* Right column of modal has our AI Summary. */}
            <div className="h-full overflow-y-auto bg-gray-900 p-6 rounded-lg">
              <h3 className="text-xl font-semibold mb-3 text-green-400">AI Summary</h3>
              <p className="text-gray-300 italic mb-6">"{fullVideoData.summary_data?.one_sentence_summary}"</p>
              <h4 className="font-semibold mb-3 text-green-400">Key Points:</h4>
              <ul className="list-disc list-inside space-y-3 text-gray-200">
                {fullVideoData.summary_data?.key_bullet_points.map((point, i) => <li key={i}>{point}</li>)}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};