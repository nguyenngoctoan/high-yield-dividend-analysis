import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';
import crypto from 'crypto';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

function generateAPIKey(): string {
  return `sk_live_${crypto.randomBytes(32).toString('hex')}`;
}

function hashAPIKey(key: string): string {
  return crypto.createHash('sha256').update(key).digest('hex');
}

function getKeyPrefix(key: string): string {
  return key.substring(0, 20);
}

function calculateExpiryDate(expiry: string): Date | null {
  if (expiry === 'never') return null;

  const days = parseInt(expiry);
  const expiryDate = new Date();
  expiryDate.setDate(expiryDate.getDate() + days);
  return expiryDate;
}

export async function GET(request: NextRequest) {
  try {
    const { data, error } = await supabase
      .from('divv_api_keys')
      .select('*')
      .order('created_at', { ascending: false });

    if (error) {
      console.error('Supabase error:', error);
      return NextResponse.json(
        { error: 'Failed to fetch API keys', detail: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json({ keys: data || [] });
  } catch (error) {
    console.error('Error fetching API keys:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { name, expiry = 'never' } = body;

    if (!name || !name.trim()) {
      return NextResponse.json(
        { error: 'Name is required' },
        { status: 400 }
      );
    }

    // Generate the API key
    const apiKey = generateAPIKey();
    const keyHash = hashAPIKey(apiKey);
    const keyPrefix = getKeyPrefix(apiKey);
    const expiresAt = calculateExpiryDate(expiry);

    // Insert into database
    const { data, error } = await supabase
      .from('divv_api_keys')
      .insert({
        name: name.trim(),
        key_hash: keyHash,
        key_prefix: keyPrefix,
        expires_at: expiresAt?.toISOString() || null,
      })
      .select()
      .single();

    if (error) {
      console.error('Supabase error:', error);
      return NextResponse.json(
        { error: 'Failed to create API key', detail: error.message },
        { status: 500 }
      );
    }

    // Return the full API key (only time it will be shown)
    return NextResponse.json({
      api_key: apiKey,
      key_data: data,
    });
  } catch (error) {
    console.error('Error creating API key:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
