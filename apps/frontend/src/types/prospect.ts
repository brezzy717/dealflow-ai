export type Tier = 'green' | 'yellow' | 'red' | 'monitor';

export interface Attribution {
  feature: string;
  label: string;
  contribution: number;
}

export interface Prospect {
  assignment_id: string;
  status: string;
  tier: Tier;
  business_name: string;
  industry: string | null;
  city: string | null;
  state: string | null;
  employee_count: number | null;
  revenue_millions: number | null;
  years_in_business: number | null;
  owner_name: string | null;
  score: number | null;
  confidence: number | null;
  explanation: string | null;
  top_positive: Attribution[];
  top_negative: Attribution[];
}

export interface ProspectsResponse {
  prospects: Prospect[];
}
