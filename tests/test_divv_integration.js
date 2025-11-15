/**
 * DIVV() Google Sheets Integration Tests
 *
 * Tests the DIVV.gs functions using seed data.
 * Run this in Google Apps Script Test environment or with clasp.
 */

// Load seed data (you'll need to paste seed_data.json content or load it)
const SEED_DATA = {
  stocks: [
    {
      symbol: "AAPL",
      price: 175.43,
      open: 174.50,
      dayHigh: 176.20,
      dayLow: 173.80,
      previousClose: 174.25,
      dividendYield: 0.52,
      dividendAmount: 0.96,
      peRatio: 28.5,
      marketCap: 2750000000000,
      volume: 52000000
    },
    {
      symbol: "MSFT",
      price: 378.91,
      dividendYield: 0.89,
      dividendAmount: 3.00,
      peRatio: 35.2
    },
    {
      symbol: "JNJ",
      dividendAmount: 4.76,
      dayHigh: 159.40,
      isAristocrat: true,
      consecutiveYears: 61
    }
  ]
};

/**
 * Test Suite Runner
 */
function runAllTests() {
  const results = {
    passed: 0,
    failed: 0,
    tests: []
  };

  console.log("=".repeat(60));
  console.log("DIVV() Integration Test Suite");
  console.log("=".repeat(60));

  // Run test categories
  testCurrentDataFreeTier(results);
  testCurrentDataPaidTier(results);
  testHistoricalData(results);
  testTierRestrictions(results);
  testErrorHandling(results);

  // Summary
  console.log("=".repeat(60));
  console.log("Test Summary:");
  console.log(`  Passed: ${results.passed}`);
  console.log(`  Failed: ${results.failed}`);
  console.log(`  Total:  ${results.passed + results.failed}`);
  console.log("=".repeat(60));

  return results;
}

/**
 * Test helper function
 */
function runTest(name, testFn, results) {
  try {
    console.log(`\nRunning: ${name}`);
    testFn();
    console.log(`  ✓ PASSED`);
    results.passed++;
    results.tests.push({ name, status: "PASSED" });
  } catch (error) {
    console.log(`  ✗ FAILED: ${error.message}`);
    results.failed++;
    results.tests.push({ name, status: "FAILED", error: error.message });
  }
}

/**
 * Assertion helper
 */
function assertEquals(actual, expected, message) {
  if (actual !== expected) {
    throw new Error(`${message}\n  Expected: ${expected}\n  Actual: ${actual}`);
  }
}

function assertClose(actual, expected, tolerance = 0.01, message) {
  if (Math.abs(actual - expected) > tolerance) {
    throw new Error(`${message}\n  Expected: ${expected} (±${tolerance})\n  Actual: ${actual}`);
  }
}

function assertContains(str, substring, message) {
  if (!str.toString().includes(substring)) {
    throw new Error(`${message}\n  String: ${str}\n  Expected to contain: ${substring}`);
  }
}

/**
 * Test Category: Current Data (Free Tier)
 */
function testCurrentDataFreeTier(results) {
  console.log("\n" + "=".repeat(60));
  console.log("Category: Current Data (Free Tier)");
  console.log("=".repeat(60));

  // Set to free tier
  if (typeof ACCOUNT_TIER !== 'undefined') {
    ACCOUNT_TIER = 'free';
  }

  runTest("Get AAPL current price", () => {
    const result = DIVV("AAPL", "price");
    assertClose(result, 175.43, 0.1, "AAPL price should match seed data");
  }, results);

  runTest("Get MSFT dividend yield", () => {
    const result = DIVV("MSFT", "dividendYield");
    assertClose(result, 0.89, 0.01, "MSFT dividend yield should match");
  }, results);

  runTest("Get JNJ dividend amount", () => {
    const result = DIVV("JNJ", "dividendAmount");
    assertClose(result, 4.76, 0.01, "JNJ dividend amount should match");
  }, results);

  runTest("Get AAPL day high", () => {
    const result = DIVV("AAPL", "dayHigh");
    assertClose(result, 176.20, 0.1, "AAPL day high should match");
  }, results);

  runTest("Get AAPL previous close", () => {
    const result = DIVV("AAPL", "previousClose");
    assertClose(result, 174.25, 0.1, "AAPL previous close should match");
  }, results);

  runTest("Get AAPL open", () => {
    const result = DIVV("AAPL", "open");
    assertClose(result, 174.50, 0.1, "AAPL open should match");
  }, results);
}

/**
 * Test Category: Current Data (Paid Tier)
 */
function testCurrentDataPaidTier(results) {
  console.log("\n" + "=".repeat(60));
  console.log("Category: Current Data (Paid Tier)");
  console.log("=".repeat(60));

  // Set to paid tier
  if (typeof ACCOUNT_TIER !== 'undefined') {
    ACCOUNT_TIER = 'paid';
  }

  runTest("Get AAPL PE ratio", () => {
    const result = DIVV("AAPL", "peRatio");
    assertClose(result, 28.5, 0.5, "AAPL PE ratio should match");
  }, results);

  runTest("Get AAPL market cap", () => {
    const result = DIVV("AAPL", "marketCap");
    // Market cap might be in billions or actual number
    assertEquals(typeof result, "number", "Market cap should be a number");
  }, results);

  runTest("Get AAPL volume", () => {
    const result = DIVV("AAPL", "volume");
    assertEquals(typeof result, "number", "Volume should be a number");
  }, results);

  runTest("Get MSFT PE ratio", () => {
    const result = DIVV("MSFT", "peRatio");
    assertClose(result, 35.2, 0.5, "MSFT PE ratio should match");
  }, results);
}

/**
 * Test Category: Historical Data
 */
function testHistoricalData(results) {
  console.log("\n" + "=".repeat(60));
  console.log("Category: Historical Data (Paid Tier)");
  console.log("=".repeat(60));

  // Set to paid tier
  if (typeof ACCOUNT_TIER !== 'undefined') {
    ACCOUNT_TIER = 'paid';
  }

  runTest("Get AAPL historical close on 2024-01-15", () => {
    const result = DIVV("AAPL", "close", "2024-01-15");
    assertClose(result, 185.59, 0.1, "Historical close should match seed data");
  }, results);

  runTest("Get AAPL historical open on 2024-01-16", () => {
    const result = DIVV("AAPL", "open", "2024-01-16");
    assertClose(result, 184.35, 0.1, "Historical open should match");
  }, results);

  runTest("Get MSFT historical close on 2024-01-15", () => {
    const result = DIVV("MSFT", "close", "2024-01-15");
    assertClose(result, 372.91, 0.1, "MSFT historical close should match");
  }, results);

  runTest("Get AAPL historical range returns array", () => {
    const result = DIVV("AAPL", "close", "2024-01-15", "2024-01-17");

    // Should return 2D array
    assertEquals(Array.isArray(result), true, "Should return an array");
    assertEquals(result.length > 1, true, "Should have multiple rows");

    // First row should be headers
    assertEquals(result[0][0], "Date", "First header should be Date");

    // Should have 3 data rows (plus header)
    assertEquals(result.length, 4, "Should have 4 rows total (1 header + 3 data)");
  }, results);
}

/**
 * Test Category: Tier Restrictions
 */
function testTierRestrictions(results) {
  console.log("\n" + "=".repeat(60));
  console.log("Category: Tier Restrictions (Free Tier)");
  console.log("=".repeat(60));

  // Set to free tier
  if (typeof ACCOUNT_TIER !== 'undefined') {
    ACCOUNT_TIER = 'free';
  }

  runTest("Free tier blocked on PE ratio", () => {
    const result = DIVV("AAPL", "peRatio");
    assertContains(result, "#UPGRADE", "Should return upgrade message");
    assertContains(result, "paid plan", "Should mention paid plan");
  }, results);

  runTest("Free tier blocked on volume", () => {
    const result = DIVV("AAPL", "volume");
    assertContains(result, "#UPGRADE", "Should return upgrade message");
  }, results);

  runTest("Free tier blocked on market cap", () => {
    const result = DIVV("AAPL", "marketCap");
    assertContains(result, "#UPGRADE", "Should return upgrade message");
  }, results);

  runTest("Free tier blocked on historical data", () => {
    const result = DIVV("AAPL", "close", "2024-01-15");
    assertContains(result, "#UPGRADE", "Should return upgrade message");
    assertContains(result, "Historical data", "Should mention historical data");
  }, results);

  runTest("Free tier blocked on DIVVDIVIDENDS", () => {
    if (typeof DIVVDIVIDENDS !== 'undefined') {
      const result = DIVVDIVIDENDS("AAPL", 12);
      assertContains(result, "#UPGRADE", "Should return upgrade message");
    }
  }, results);

  runTest("Free tier blocked on DIVVARISTOCRAT", () => {
    if (typeof DIVVARISTOCRAT !== 'undefined') {
      const result = DIVVARISTOCRAT("JNJ");
      assertContains(result, "#UPGRADE", "Should return upgrade message");
    }
  }, results);
}

/**
 * Test Category: Error Handling
 */
function testErrorHandling(results) {
  console.log("\n" + "=".repeat(60));
  console.log("Category: Error Handling");
  console.log("=".repeat(60));

  runTest("Invalid symbol returns error", () => {
    const result = DIVV("INVALID", "price");
    assertContains(result.toString(), "#ERROR", "Should return error for invalid symbol");
  }, results);

  runTest("Invalid attribute returns N/A", () => {
    const result = DIVV("AAPL", "invalidAttribute");
    assertContains(result.toString(), "#N/A", "Should return #N/A for invalid attribute");
  }, results);

  runTest("Empty symbol returns error", () => {
    const result = DIVV("", "price");
    assertContains(result.toString(), "#ERROR", "Should return error for empty symbol");
  }, results);

  runTest("Null symbol returns error", () => {
    const result = DIVV(null, "price");
    assertContains(result.toString(), "#ERROR", "Should return error for null symbol");
  }, results);
}

/**
 * Performance Test
 */
function testPerformance() {
  console.log("\n" + "=".repeat(60));
  console.log("Performance Tests");
  console.log("=".repeat(60));

  // Test cache performance
  const start1 = new Date().getTime();
  DIVV("AAPL", "price");
  const time1 = new Date().getTime() - start1;
  console.log(`First call (no cache): ${time1}ms`);

  const start2 = new Date().getTime();
  DIVV("AAPL", "price");
  const time2 = new Date().getTime() - start2;
  console.log(`Second call (cached): ${time2}ms`);

  if (time2 < time1) {
    console.log("✓ Cache is working (second call faster)");
  } else {
    console.log("⚠ Cache might not be working");
  }
}

/**
 * Integration Test: Real-World Use Cases
 */
function testRealWorldUseCases(results) {
  console.log("\n" + "=".repeat(60));
  console.log("Real-World Use Cases");
  console.log("=".repeat(60));

  // Set to paid tier for these tests
  if (typeof ACCOUNT_TIER !== 'undefined') {
    ACCOUNT_TIER = 'paid';
  }

  runTest("Calculate portfolio return", () => {
    const currentPrice = DIVV("AAPL", "price");
    const purchasePrice = 185.59; // From historical data
    const returnPct = ((currentPrice - purchasePrice) / purchasePrice) * 100;

    assertEquals(typeof returnPct, "number", "Return should be a number");
    console.log(`    Portfolio return: ${returnPct.toFixed(2)}%`);
  }, results);

  runTest("Calculate annual dividend income", () => {
    const shares = 100;
    const dividendAmount = DIVV("AAPL", "dividendAmount");
    const annualIncome = shares * dividendAmount;

    assertEquals(typeof annualIncome, "number", "Income should be a number");
    console.log(`    Annual income from 100 shares: $${annualIncome.toFixed(2)}`);
  }, results);

  runTest("Compare dividend yields", () => {
    const aaplYield = DIVV("AAPL", "dividendYield");
    const msftYield = DIVV("MSFT", "dividendYield");

    assertEquals(typeof aaplYield, "number", "AAPL yield should be number");
    assertEquals(typeof msftYield, "number", "MSFT yield should be number");

    console.log(`    AAPL yield: ${aaplYield}%`);
    console.log(`    MSFT yield: ${msftYield}%`);
  }, results);
}

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    runAllTests,
    testCurrentDataFreeTier,
    testCurrentDataPaidTier,
    testHistoricalData,
    testTierRestrictions,
    testErrorHandling
  };
}
