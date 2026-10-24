export interface StoreItem {
  id: number;
  name: string;
  status: 'active' | 'archived' | 'draft';
}

export interface PaymentRequest {
  amount: number;
  currency: string;
}
