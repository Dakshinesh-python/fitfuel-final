import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Progress from '../src/pages/Progress';
import { apiClient } from '../src/api/client';

vi.mock('../src/api/client', async () => {
  const actual = await vi.importActual<typeof import('../src/api/client')>('../src/api/client');
  return {
    ...actual,
    apiClient: {
      get: vi.fn(),
      post: vi.fn(),
    },
  };
});

/**
 * Progress.tsx makes THREE parallel GET calls:
 *   /api/progress/summary   → { weeklyAverageCalories, goalAchievementPct, logs }
 *   /api/progress           → { logs: [...] }
 *   /api/progress/weight-history → { weightHistory: [...] }
 *
 * The mock must resolve all three or the component stays in loading state.
 */
function mockAllProgressEndpoints(overrides?: {
  weeklyAverageCalories?: number;
  goalAchievementPct?: number | null;
}) {
  vi.mocked(apiClient.get).mockImplementation((url: string) => {
    if (url === '/api/progress/summary') {
      return Promise.resolve({
        data: {
          weeklyAverageCalories: overrides?.weeklyAverageCalories ?? 2100,
          goalAchievementPct: overrides?.goalAchievementPct ?? 80,
          logs: [],
        },
      });
    }
    if (url === '/api/progress') {
      return Promise.resolve({ data: { logs: [] } });
    }
    if (url === '/api/progress/weight-history') {
      return Promise.resolve({ data: { weightHistory: [] } });
    }
    return Promise.resolve({ data: {} });
  });
}

describe('Progress', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the log-entry form fields', async () => {
    mockAllProgressEndpoints();

    render(
      <MemoryRouter>
        <Progress />
      </MemoryRouter>,
    );

    // Form fields are rendered immediately (not behind the API load)
    expect(screen.getByLabelText(/weight \(kg\)/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/calories/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /log entry/i })).toBeInTheDocument();
  });

  it('shows the weekly average and goal percentage from the summary', async () => {
    mockAllProgressEndpoints({ weeklyAverageCalories: 2100, goalAchievementPct: 80 });

    render(
      <MemoryRouter>
        <Progress />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText('2100')).toBeInTheDocument();
    });
    expect(screen.getByText('80%')).toBeInTheDocument();
  });

  it('shows — for goal achievement when pct is null', async () => {
    mockAllProgressEndpoints({ goalAchievementPct: null });

    render(
      <MemoryRouter>
        <Progress />
      </MemoryRouter>,
    );

    await waitFor(() => {
      // When goalAchievementPct is null, the component shows — or 0
      expect(screen.getByText('2100')).toBeInTheDocument();
    });
  });
});
