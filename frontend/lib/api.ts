import axios from 'axios';
import { Episode, EpisodeCreateRequest, ProcessingTask, ChapterSyncRequest, Transcript, ShowNotesItem } from '@/types';

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const episodeApi = {
  list: async (): Promise<Episode[]> => {
    const response = await api.get('/episodes');
    return response.data;
  },

  get: async (id: string): Promise<Episode> => {
    const response = await api.get(`/episodes/${id}`);
    return response.data;
  },

  create: async (data: FormData): Promise<Episode> => {
    const response = await api.post('/episodes', data, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  updateShowNotes: async (id: string, items: ShowNotesItem[]): Promise<Episode> => {
    const response = await api.patch(`/episodes/${id}/show-notes`, items);
    return response.data;
  },
};

export const transcriptApi = {
  get: async (episodeName: string): Promise<Transcript> => {
    const response = await api.get(`/transcripts/${episodeName}`);
    return response.data;
  },

  getRaw: async (episodeName: string): Promise<any> => {
    const response = await api.get(`/transcripts/${episodeName}/raw`);
    return response.data;
  },
};

export const processingApi = {
  getStatus: async (taskId: string): Promise<ProcessingTask> => {
    const response = await api.get(`/processing/status/${taskId}`);
    return response.data;
  },

  retry: async (taskId: string): Promise<{ message: string; task_id: string }> => {
    const response = await api.post(`/processing/retry/${taskId}`);
    return response.data;
  },
};

export const chapterApi = {
  sync: async (data: ChapterSyncRequest): Promise<{ message: string; task_id: string }> => {
    const response = await api.post('/chapters/sync', data);
    return response.data;
  },
};