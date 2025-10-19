import { useState, useEffect } from 'react';
import type { Video, Digest } from './interfaces';
import { VideoModal } from './VideoModal';
import { ChatWidget } from './ChatWidget';

const API_BASE_URL = 'http://localhost:8000'; // Base URL for both API and audio files.

function App() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [digests, setDigests] = useState<Digest[]>([]);
  const [selectedVideo, setSelectedVideo] = useState<Video | null>(null);

  // Fetch all data when the component first loads.
  useEffect(() => {
    const fetchData = async () => {
      try {
        const videosResponse = await fetch(`${API_BASE_URL}/api/videos/listVideos`);
        const allVideos: Video[] = await videosResponse.json();

        // Show only completed videos, newest first.
        setVideos(allVideos.filter(v => v.status === 'COMPLETED').reverse());

        const digestsResponse = await fetch(`${API_BASE_URL}/api/digests`);
        const allDigests: Digest[] = await digestsResponse.json();
        setDigests(allDigests.filter(d => d.status === 'COMPLETED').reverse());
      } catch (error) {
        console.error("Failed to fetch initial dashboard data:", error);
      }
    };
    fetchData();
  }, []);

  const handleVideoClick = (video: Video) => {
    setSelectedVideo(video);
  };
  
  // A helper function to build the correct, full URL for the audio file.
  const getAudioUrl = (localPath: string) => {
    if (!localPath) return '';

    // This converts '/path/to/backend/tmp/file.mp3' to 'http://localhost:8000/media/file.mp3',
    // using the url config set up on the Django backend.
    const filename = localPath.split('/').pop();
    return `${API_BASE_URL}/media/${filename}`;
  }

  return (
    <div className="bg-gray-900 text-white min-h-screen font-sans">
      <main className="container mx-auto px-4 py-8">
        <header className="text-center mb-12">
          <h1 className="text-5xl font-extrabold mb-2 text-green-400">Seahawks Press Portal</h1>
          <p className="text-xl text-gray-400">Your daily, AI-powered briefing on the latest Seahawks press conferences.</p>
        </header>
        
        <section>
          <h2 className="text-3xl font-bold border-b-2 border-green-400 pb-2 mb-6">Press Conferences</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {videos.map(video => (
              <div key={video.id} onClick={() => handleVideoClick(video)} className="cursor-pointer bg-gray-800 
              rounded-lg overflow-hidden shadow-lg hover:shadow-green-500/20 hover:-translate-y-2 transition-all 
              duration-300 group">
                <div className="relative">
                  <img src={video.thumbnail_url} alt={video.title} className="w-full h-48 object-cover"/>
                  <div className="absolute inset-0 bg-black opacity-40 group-hover:opacity-20 transition-opacity"></div>
                </div>
                <div className="p-4">
                  <p className="text-sm font-bold text-green-400">{video.speaker || 'Press Conference'}</p>
                  <h3 className="font-semibold text-lg truncate mt-1 group-hover:text-green-300 
                  transition-colors">{video.title}</h3>
                  <p className="text-xs text-gray-500 mt-2">{new Date(video.published_at).toLocaleDateString()}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="mt-16">
          <h2 className="text-3xl font-bold border-b-2 border-green-400 pb-2 mb-6">Daily Digests</h2>
          <div className="space-y-4">
            {digests.map(digest => (
              <div key={digest.id} className="bg-gray-800 p-4 rounded-lg flex flex-col sm:flex-row items-center 
              justify-between gap-4">
                <p className="font-semibold text-lg">Daily Digest: {new Date(digest.digest_date).toLocaleDateString()}</p>
                <audio controls src={getAudioUrl(digest.audio_url)} className="w-full sm:w-1/2"></audio>
              </div>
            ))}
          </div>
        </section>
      </main>

      {selectedVideo && <VideoModal video={selectedVideo} onClose={() => setSelectedVideo(null)} />}
      <ChatWidget />
    </div>
  );
}

export default App;
