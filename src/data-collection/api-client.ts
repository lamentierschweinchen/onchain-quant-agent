import axios, { AxiosInstance } from 'axios';
import { config } from '../config';
import { Account, Transaction } from '../types';

export class MultiversXApiClient {
    private client: AxiosInstance;
    private gatewayClient: AxiosInstance;

    constructor() {
        this.client = axios.create({
            baseURL: config.api.baseUrl,
            timeout: config.api.timeout,
        });

        this.gatewayClient = axios.create({
            baseURL: config.api.gatewayUrl,
            timeout: config.api.timeout,
        });

        // Rate limiting interceptor if needed (simple delay)
        this.client.interceptors.response.use(async (response) => {
            await new Promise(resolve => setTimeout(resolve, config.api.rateLimitDelay));
            return response;
        });
    }

    async getAccount(address: string): Promise<Account> {
        try {
            const response = await this.client.get<Account>(`/accounts/${address}`);
            return response.data;
        } catch (error) {
            console.error(`Error fetching account ${address}:`, error);
            throw error;
        }
    }

    async getTransactions(address: string, limit: number = 20): Promise<Transaction[]> {
        try {
            const response = await this.client.get<Transaction[]>(`/accounts/${address}/transactions`, {
                params: { size: limit }
            });
            return response.data;
        } catch (error) {
            console.error(`Error fetching transactions for ${address}:`, error);
            throw error;
        }
    }

    async getNetworkStats(): Promise<any> {
        try {
            const response = await this.client.get('/economics');
            return response.data;
        } catch (error) {
            console.error('Error fetching economics:', error);
            throw error;
        }
    }

    // Generic fetch for other modules
    async fetch(endpoint: string, params: any = {}): Promise<any> {
        const response = await this.client.get(endpoint, { params });
        return response.data;
    }
}
