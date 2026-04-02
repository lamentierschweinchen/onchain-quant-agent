import { config } from './config';
import { QuantDatabase } from './storage/db';
import { MultiversXApiClient } from './data-collection/api-client';

async function main() {
    console.log('Testing setup...');
    console.log('Config loaded:', config.api.baseUrl);

    const db = new QuantDatabase();
    console.log('Database initialized.');

    const client = new MultiversXApiClient();
    console.log('API Client initialized.');

    try {
        const stats = await client.getNetworkStats();
        console.log('Network Stats fetch successful:', stats ? 'OK' : 'Empty');
    } catch (e) {
        console.error('API Connection failed (expected if network issues):', (e as Error).message);
    }
}

main().catch(console.error);
