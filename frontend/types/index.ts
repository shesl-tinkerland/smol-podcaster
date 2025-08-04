export interface Episode {
  id: string;
  name: string;
  speakers_count: number;
  status: ProcessingStatus;
  created_at: string;
  updated_at: string;
  file_path?: string;
  transcript_path?: string;
  results_path?: string;
  show_notes?: ShowNotesItem[];
  chapters?: string;
  writeup?: string;
  error_message?: string;
}

export enum ProcessingStatus {
  PENDING = "pending",
  PROCESSING = "processing",
  COMPLETED = "completed",
  FAILED = "failed"
}

export interface ShowNotesItem {
  text: string;
  url?: string;
}

export interface EpisodeCreateRequest {
  name: string;
  speakers_count: number;
  file?: File;
  url?: string;
  transcript_only: boolean;
  generate_extra: boolean;
}

export interface ProcessingTask {
  task_id: string;
  episode_id: string;
  status: ProcessingStatus;
  progress?: number;
  current_step?: string;
  error_message?: string;
}

export interface ChapterSyncRequest {
  audio_name: string;
  video_name: string;
  chapters: string;
}

export interface Transcript {
  episode_name: string;
  transcript: string;
}