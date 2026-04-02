// Core Data Models

export interface Account {
    address: string;
    balance: string;
    userName?: string;
    shard?: number;
    txCount?: number;
    developerReward?: string;
    totalType?: 'whale' | 'institution' | 'retail' | 'contract';
}

export interface Transaction {
    hash: string;
    timestamp: number;
    sender: string;
    receiver: string;
    value: string;
    fee?: string;
    gasLimit?: number;
    gasPrice?: number;
    status: string;
    data?: string;
    tokenIdentifier?: string;
    tokenValue?: string;
    function?: string;
}

export interface TokenTransfer {
    tokenIdentifier: string;
    sender: string;
    receiver: string;
    value: string; // BigInt string
    decimals: number;
    timestamp: number;
    txHash: string;
}

export interface StakeEvent {
    delegator: string;
    validator: string;
    value: string;
    action: 'stake' | 'unstake' | 'redelegate';
    timestamp: number;
    txHash: string;
}

// Analysis Models

export interface AnalysisResult {
    significanceScore: number; // 0-100
    type: 'whale_movement' | 'staking_change' | 'token_flow' | 'defi_activity' | 'anomaly';
    severity: 'critical' | 'high' | 'medium' | 'low';
    summary: string;
    data: any;
    timestamp: number;
}

export interface Pattern {
    id: string;
    name: string;
    description: string;
    confidence: number;
    frequency: number;
    lastSeen: number;
    indicators: string[];
}

export interface WeeklyReport {
    id: string;
    periodStart: number;
    periodEnd: number;
    generatedAt: number;
    executiveSummary: string;
    metrics: {
        totalVolume: string;
        topGainers: string[];
        riskLevel: 'high' | 'medium' | 'low';
    };
    significantEvents: AnalysisResult[];
    trends: string[];
}

// Config Types
export interface AgentConfig {
    api: {
        baseUrl: string;
        gatewayUrl: string;
        timeout: number;
        rateLimitDelay: number;
    };
    monitoring: {
        pollIntervalMs: number;
        maxQueueSize: number;
    };
    analysis: {
        whaleThreshold: number;
        largeTransactionThreshold: number;
        significantMovementUsd: number;
    };
    database: {
        path: string;
    };
    notifications: {
        slack: { enabled: boolean; webhookUrl: string };
        email: { enabled: boolean; from: string; to: string[] };
    };
}
