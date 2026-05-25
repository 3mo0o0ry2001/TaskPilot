# TaskPilot - Error Analysis Notes

## Day 1 - Manual Trace Reading

### ✅ Working Well
- Chained tool calls (find_contact → send_email)
- Relative date calculation (tomorrow → correct ISO date)
- Contact not found → stops correctly, doesn't send

### ❌ Issues Found
1. **Over-helpfulness** — offers unrequested actions after completing task
   - Component: System Prompt
2. **XML tags leaking** in output (<message>, <contact_search_result>)
   - Component: System Prompt / Post-processing
3. **Illogical fallback option** — suggests sending email without address
   - Component: System Prompt