import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import EpisodesPage from '../page';
import { episodeApi } from '@/lib/api';
import { ProcessingStatus } from '@/types';

// Mock the API
jest.mock('@/lib/api', () => ({
  episodeApi: {
    list: jest.fn()
  }
}));

// Mock the Sidebar component
jest.mock('@/components/sidebar', () => ({
  Sidebar: () => <div>Sidebar</div>
}));

// Mock next/link
jest.mock('next/link', () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
});

const createQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

describe('EpisodesPage', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = createQueryClient();
    jest.clearAllMocks();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );

  it('renders the page title', async () => {
    (episodeApi.list as jest.Mock).mockResolvedValue([]);

    render(<EpisodesPage />, { wrapper });

    expect(screen.getByText('Edit Episodes')).toBeInTheDocument();
  });

  it('shows loading state initially', () => {
    (episodeApi.list as jest.Mock).mockImplementation(() => new Promise(() => {}));

    render(<EpisodesPage />, { wrapper });

    expect(screen.getByText('Loading episodes...')).toBeInTheDocument();
  });

  it('displays episodes when data is loaded', async () => {
    const mockEpisodes = [
      {
        id: '1',
        name: 'Episode 1',
        speakers_count: 2,
        status: ProcessingStatus.COMPLETED,
        created_at: '2024-01-01T00:00:00',
        updated_at: '2024-01-01T00:00:00'
      },
      {
        id: '2',
        name: 'Episode 2',
        speakers_count: 3,
        status: ProcessingStatus.PROCESSING,
        created_at: '2024-01-02T00:00:00',
        updated_at: '2024-01-02T00:00:00'
      }
    ];

    (episodeApi.list as jest.Mock).mockResolvedValue(mockEpisodes);

    render(<EpisodesPage />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Episode 1')).toBeInTheDocument();
      expect(screen.getByText('Episode 2')).toBeInTheDocument();
    });

    expect(screen.getByText('2 speakers')).toBeInTheDocument();
    expect(screen.getByText('3 speakers')).toBeInTheDocument();
  });

  it('shows empty state when no episodes', async () => {
    (episodeApi.list as jest.Mock).mockResolvedValue([]);

    render(<EpisodesPage />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('No episodes found.')).toBeInTheDocument();
    });
  });

  it('displays correct status badges', async () => {
    const mockEpisodes = [
      {
        id: '1',
        name: 'Episode 1',
        speakers_count: 2,
        status: ProcessingStatus.COMPLETED,
        created_at: '2024-01-01T00:00:00',
        updated_at: '2024-01-01T00:00:00'
      },
      {
        id: '2',
        name: 'Episode 2',
        speakers_count: 2,
        status: ProcessingStatus.FAILED,
        created_at: '2024-01-02T00:00:00',
        updated_at: '2024-01-02T00:00:00'
      }
    ];

    (episodeApi.list as jest.Mock).mockResolvedValue(mockEpisodes);

    render(<EpisodesPage />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Completed')).toBeInTheDocument();
      expect(screen.getByText('Failed')).toBeInTheDocument();
    });
  });

  it('shows edit link only for completed episodes', async () => {
    const mockEpisodes = [
      {
        id: '1',
        name: 'Episode 1',
        speakers_count: 2,
        status: ProcessingStatus.COMPLETED,
        created_at: '2024-01-01T00:00:00',
        updated_at: '2024-01-01T00:00:00'
      },
      {
        id: '2',
        name: 'Episode 2',
        speakers_count: 2,
        status: ProcessingStatus.PROCESSING,
        created_at: '2024-01-02T00:00:00',
        updated_at: '2024-01-02T00:00:00'
      }
    ];

    (episodeApi.list as jest.Mock).mockResolvedValue(mockEpisodes);

    render(<EpisodesPage />, { wrapper });

    await waitFor(() => {
      const editLinks = screen.getAllByText('Edit Show Notes');
      expect(editLinks).toHaveLength(1);
      expect(editLinks[0].closest('a')).toHaveAttribute('href', '/episodes/1/edit');
    });
  });
});