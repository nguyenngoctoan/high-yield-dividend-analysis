# 🚨 IMPORTANT REMINDER FOR CLAUDE

## Always Update Port 3000 (Docs Site)

When making changes to the API or pricing system, **ALWAYS ensure changes are reflected on port 3000** (the Next.js docs site), not just port 8000 (the API).

### Ports Overview:
- **Port 8000**: FastAPI backend (API endpoints)
- **Port 3000**: Next.js docs site (User-facing documentation and UI)

### Both Servers Must Be Running:

```bash
# Terminal 1: API Server (Port 8000)
python3 -m uvicorn api.main:app --reload --port 8000

# Terminal 2: Docs Site (Port 3000)
cd docs-site
npm run dev
```

### What Lives Where:

#### Port 8000 (API Backend):
- `/v1/stocks`, `/v1/dividends`, `/v1/prices`, etc.
- `/v1/bulk/*` - Bulk endpoints
- `/auth/*` - Authentication endpoints
- Rate limiting middleware
- Tier enforcement
- Database operations

#### Port 3000 (Docs Site - User-Facing):
- `/` - Homepage
- `/pricing` - **Pricing page** (VERY IMPORTANT!)
- `/api` - API documentation
- `/examples` - Code examples
- `/api-keys` - API key management UI
- `/api-reference` - API reference
- Header navigation
- All user-facing content

### When User Says "I Don't See Changes":

1. ✅ **Check port 3000 first** (docs site) - This is what users see!
2. ✅ Verify both servers are running
3. ✅ Check browser is accessing http://localhost:3000 (not 8000)
4. ✅ Verify hot-reload worked (check terminal logs)
5. ✅ Clear browser cache if needed

### Common Mistakes to Avoid:

❌ Only checking port 8000 (API) when user is viewing port 3000 (docs)
❌ Making changes to `/api` files but not updating `/docs-site` files
❌ Forgetting that pricing page lives in `docs-site/app/pricing/page.tsx`
❌ Assuming API changes automatically reflect in docs site

### Quick Verification:

```bash
# Check both servers are up
curl http://localhost:8000/health  # Should return 200
curl http://localhost:3000  # Should return 200

# View pricing page
open http://localhost:3000/pricing
```

### Files to Remember:

**Pricing-related files:**
- `docs/PRICING_TIERS.md` - Pricing documentation
- `docs-site/app/pricing/page.tsx` - **User-facing pricing page**
- `migrations/update_pricing_tiers_v2.sql` - Database schema
- `api/middleware/rate_limiter.py` - Rate limiting
- `api/middleware/tier_enforcer.py` - Tier enforcement
- `api/routers/bulk.py` - Bulk endpoints

**Always check the docs site when making user-facing changes!**

---

**Last Updated**: 2025-11-14
**Remember**: Port 3000 is what users see. Always verify changes there!
