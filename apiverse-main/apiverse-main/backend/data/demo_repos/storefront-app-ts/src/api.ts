import { StoreItem } from './types';

export const API_BASE = 'https://api.store.example.com';

export async function fetchStoreItems(): Promise<StoreItem[]> {
  const response = await fetch(`${API_BASE}/v1/items`);
  if (!response.ok) {
    throw new Error(`Failed to fetch items: ${response.statusText}`);
  }
  const data = await response.json();
  return data.items.map((item: any) => ({
    id: item.id,
    name: item.name,
    status: item.status,
  }));
}

export async function deleteStoreItem(itemId: number): Promise<boolean> {
  const response = await fetch(`${API_BASE}/v1/items?id=${itemId}`, {
    method: 'DELETE',
  });
  return response.status === 204;
}

export async function syncLegacy(): Promise<any> {
  const response = await fetch(`${API_BASE}/v1/legacy`);
  return response.json();
}
