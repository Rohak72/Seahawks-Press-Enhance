// frontend/src/interfaces.ts
export interface WordSegment {
  start: number;
  end: number;
  text: string;
}

export interface Segment {
  start: number;
  end: number;
  text: string;
  speaker: string;
}

export interface TranscriptData {
  segments: Segment[]; // Simplified for the dashboard
  word_segments: WordSegment[];
}

export interface Video {
  id: number;
  youtube_url: string;
  status: string;
  title: string;
  thumbnail_url: string;
  published_at: string;
  speaker: string;
  summary_data?: {
    title: string;
    one_sentence_summary: string;
    key_bullet_points: string[];
  };
  transcript_data?: TranscriptData;
}

export interface Digest {
  id: number;
  digest_date: string;
  status: string;
  audio_url: string;
}