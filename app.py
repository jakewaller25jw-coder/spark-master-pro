import streamlit as st
from google import genai
from google.genai import types
import json
import os

# -----------------------------------------------------------------------------
# DATABASE MANAGEMENT (Auto-Learning Memory Engine)
# -----------------------------------------------------------------------------
DB_FILE = "spark_store_database.json"

def load_store_db():
    """Loads existing product location records across stores."""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_to_store_db(new_items, store_number="1168"):
    """Saves or updates item modular locations automatically in local memory."""
    db = load_store_db()
    if store_number not in db:
        db[store_number] = {}
        
    for item in new_items:
        key = item.get("upc") or item.get("name")
        db[store_number][key] = {
            "name": item.get("name"),
            "aisle": item.get("aisle"),
            "section": item.get("section"),
            "modular": item.get("modular", "N/A"),
            "size": item.get("size"),
            "price": item.get("price"),
            "upc": item.get("upc"),
            "substitutes": item.get("substitutes", [])
        }
        
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)
    return len(db[store_number])

# -----------------------------------------------------------------------------
# STREAMLIT MOBILE UI CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Spark Master Pro",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Mobile Styling
st.markdown("""
    <style>
    .stApp { max-width: 650px; margin: 0 auto; }
    .main-header { text-align: center; color: #0071dc; padding-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2 class='main-header'>⚡ Spark Master Pro</h2>", unsafe_allow_html=True)
st.caption("Auto-Learning Route Planner, Barcode Hub & Smart Substitution Engine")

# -----------------------------------------------------------------------------
# SIDEBAR CONFIGURATION & ACCESS CONTROL
# -----------------------------------------------------------------------------
st.sidebar.header("⚙️ App Controls & Settings")

# Access Key Lock (For Monetization / Restricting Access)
user_passcode = st.sidebar.text_input("App Access Code", type="password")
api_key = st.sidebar.text_input("Gemini API Key", type="password")

store_id = st.sidebar.text_input("Store ID #", value="1168")
store_db = load_store_db()
saved_skus = len(store_db.get(store_id, {}))
st.sidebar.metric(f"Saved SKUs for Store #{store_id}", saved_skus)

# Passcode Authorization
if user_passcode != "SPARKPRO2026":
    st.warning("🔒 Please enter a valid App Access Code to use Spark Master Pro.")
    st.info("Tip: Default passcode is set to `SPARKPRO2026` in sidebar.")
    st.stop()

if not api_key:
    st.info("💡 Enter your free Gemini API key in the sidebar to activate the AI vision parser.")
    st.stop()

# -----------------------------------------------------------------------------
# SCREENSHOT PROCESSING ENGINE
# -----------------------------------------------------------------------------
uploaded_image = st.file_uploader("📷 Upload Spark Offer Screenshot", type=["png", "jpg", "jpeg"])

if uploaded_image:
    st.info(f"Analyzing screenshot & syncing memory for Store #{store_id}...")
    
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    Extract all shopping items from this Walmart Spark Driver screenshot for Store #{store_id}.
    
    For each item, extract:
    1. Spark Item Index (1, 2, 3...) strictly matching screen sequence top-to-bottom.
    2. Aisle Code (e.g., "G10", "A26", "GR1", "Z1").
    3. Section Number (e.g., "3", "12").
    4. Modular Shelf Sequence Number if visible.
    5. Full Product Name.
    6. Size / Weight / Quantity.
    7. Price.
    8. Estimated 12-digit UPC barcode string (lookup or valid UPC-A format).

    ALSO, generate 2 SAME-AISLE substitutes for each item adhering to these STRICT GUARDRAILS:
    
    STRICT SUBSTITUTION GUARDRAILS:
    1. MAXIMUM PRICE CEILING: REJECT any substitute where total cost exceeds 1.9x the original item's price.
    2. PRIORITIZE CHEAPER OPTIONS FIRST: Always offer cheaper, practical alternatives first (e.g., store brand / Great Value, or smaller unit).
    3. SMART VALUE, BULK & MULTI-PACK COMBOS:
       - Bulk Size Upgrade: If a larger size/pack is on sale or slightly higher (e.g., 24-pack for $9.97 vs 12-pack for $8.97), offer it as a top "Smart Value Upgrade".
       - Quantity Multi-Pack Math: If smaller individual units are priced low (e.g., $1.00 for 8 oz vs $3.97 for 16 oz), calculate multi-pack options:
            a) Equal Volume Deal: (e.g., 2x 8 oz for $2.00 -> Saves customer money for same volume)
            b) Double Volume Deal: (e.g., 4x 8 oz for $4.00 -> Double product for minimal price difference)
    4. STRICT SUGAR & DIETARY MATCH (CRITICAL):
       - Full Sugar / Regular MUST match Full Sugar / Regular.
       - Zero Sugar / Sugar-Free / Diet MUST match Zero Sugar / Sugar-Free / Diet.
       - NEVER swap Regular for Sugar-Free or Sugar-Free for Regular under any circumstances.
    5. SAME AISLE LOCATION: Substitutes MUST be items located in the exact same aisle/department.

    Return ONLY a raw JSON array of objects with these exact keys:
    [
      {{
        "sparkIndex": 1,
        "name": "Item Name",
        "aisle": "G10",
        "section": "3",
        "modular": "004",
        "size": "3 oz",
        "qty": 1,
        "price": "$6.96",
        "upc": "079400018709",
        "substitutes": [
          {{
            "name": "Sub Name",
            "size": "Sub Size",
            "price": "$0.00",
            "upc": "000000000000",
            "note": "Math or Value Note"
          }}
        ]
      }}
    ]
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                types.Part.from_bytes(
                    data=uploaded_image.getvalue(),
                    mime_type=uploaded_image.type,
                ),
                prompt
            ]
        )
        
        raw_text = response.text.replace('```json', '').replace('```', '').strip()
        items = json.loads(raw_text)

        # Update Store Database
        total_skus = save_to_store_db(items, store_id)
        st.success(f"Route Generated! {len(items)} Items Mapped (Store #{store_id} DB: {total_skus} SKUs)")

        # Render Interactive Web Interface
        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <script src="https://cdn.jsdelivr.net/npm/jsbarcode@3.11.5/dist/JsBarcode.all.min.js"></script>
          <style>
            :root {{ --primary: #0071dc; --success: #10b981; --bg: #f8fafc; --card: #ffffff; --border: #cbd5e1; }}
            body {{ font-family: -apple-system, system-ui, sans-serif; background: var(--bg); margin:0; padding:8px; padding-bottom:40px; }}
            .mode-btn {{ width:100%; padding:14px; background:var(--primary); color:white; border:none; border-radius:10px; font-weight:800; font-size:15px; margin-bottom:12px; cursor:pointer; box-shadow:0 2px 4px rgba(0,0,0,0.1); }}
            .scan-mode {{ background:var(--success) !important; }}
            .card {{ background:var(--card); padding:12px; border-radius:10px; border:1px solid var(--border); margin-bottom:10px; box-shadow:0 1px 3px rgba(0,0,0,0.05); }}
            .badge {{ background:#e0f2fe; color:#0369a1; padding:3px 8px; border-radius:6px; font-weight:700; font-size:12px; }}
            .mod-badge {{ background:#fef3c7; color:#92400e; padding:3px 8px; border-radius:6px; font-weight:700; font-size:12px; margin-left:4px; }}
            .title {{ font-weight:700; font-size:15px; margin:6px 0 2px 0; color:#0f172a; }}
            .meta {{ color:#64748b; font-size:13px; margin-bottom:6px; }}
            
            /* Substitution Drawer */
            .btn-oos {{ background:#fee2e2; color:#991b1b; border:1px solid #fca5a5; padding:6px 10px; border-radius:6px; font-weight:700; font-size:12px; cursor:pointer; width:100%; margin-top:4px; }}
            .sub-drawer {{ display:none; background:#f1f5f9; border:1px dashed #94a3b8; padding:10px; border-radius:8px; margin-top:8px; }}
            .sub-card {{ background:white; padding:8px; border-radius:6px; margin-top:6px; text-align:center; border:1px solid #cbd5e1; }}
            
            /* Barcode Styling */
            .barcode-box {{ text-align:center; background:#fafafa; border:1px solid #e2e8f0; padding:8px; margin-top:8px; border-radius:8px; }}
            svg.bc {{ width:100%; height:45px; }}
            svg.bc-sub {{ width:100%; height:35px; }}
            .upc-num {{ font-family:monospace; font-size:12px; font-weight:700; color:#334155; }}
          </style>
        </head>
        <body>
          <button id="toggleBtn" class="mode-btn" onclick="switchMode()">📱 Switch to Phase 2: Spark Barcode Scanner Order</button>
          <div id="list"></div>

          <script>
            const items = {json.dumps(items)};
            let mode = 'PICK';

            function render() {{
              const container = document.getElementById('list');
              const btn = document.getElementById('toggleBtn');
              container.innerHTML = '';

              if(mode === 'PICK') {{
                btn.innerText = "📱 Switch to Phase 2: Spark Barcode Scanner Order";
                btn.classList.remove('scan-mode');
                
                // Sort by Aisle Single-Pass Route
                let pickList = [...items].sort((a,b) => a.aisle.localeCompare(b.aisle));
                pickList.forEach((item, idx) => {{
                  const drawerId = "drawer-" + idx;
                  
                  let subHtml = '';
                  if (item.substitutes && item.substitutes.length > 0) {{
                    item.substitutes.forEach((sub, sIdx) => {{
                      const subBcId = `sub-bc-${{idx}}-${{sIdx}}`;
                      subHtml += `
                        <div class="sub-card">
                          <div style="font-weight:700; font-size:12px; color:#0f172a;">${{sub.name}}</div>
                          <div style="font-size:11px; color:#0369a1; font-weight:600;">${{sub.size}} • ${{sub.price}}</div>
                          <div style="font-size:11px; color:#16a34a; font-weight:700; margin:2px 0;">${{sub.note || ''}}</div>
                          <svg id="${{subBcId}}" class="bc-sub"></svg>
                          <div class="upc-num">UPC: ${{sub.upc}}</div>
                        </div>
                      `;
                      setTimeout(() => {{
                        JsBarcode("#" + subBcId, sub.upc, {{format: "UPC", width: 1.8, height: 35, displayValue: false}});
                      }}, 50);
                    }});
                  }}

                  container.innerHTML += `
                    <div class="card">
                      <span class="badge">Aisle ${{item.aisle}} | Sec ${{item.section}}</span>
                      <span class="mod-badge">MOD #${{item.modular}}</span>
                      <span style="font-size:11px; color:#64748b; margin-left:6px;">Spark #${{item.sparkIndex}}</span>
                      <div class="title">${{item.name}}</div>
                      <div class="meta">${{item.size}} • Qty: <strong>${{item.qty}}</strong> • ${{item.price}}</div>
                      <button class="btn-oos" onclick="toggleDrawer('${{drawerId}}')">⚠️ Item OOS? Show Same-Aisle Substitutes</button>
                      <div id="${{drawerId}}" class="sub-drawer">
                        <div style="font-size:12px; font-weight:800; color:#0f172a;">Smart Same-Aisle Substitutes:</div>
                        ${{subHtml}}
                      </div>
                    </div>
                  `;
                }});
              }} else {{
                btn.innerText = "🛒 Return to Single-Pass Store Route";
                btn.classList.add('scan-mode');
                
                // Sort strictly by original Spark Order (#1, #2, #3...)
                let scanList = [...items].sort((a,b) => a.sparkIndex - b.sparkIndex);
                scanList.forEach(item => {{
                  const bcId = "bc-" + item.sparkIndex;
                  container.innerHTML += `
                    <div class="card">
                      <span class="badge" style="background:#10b981; color:white;">SPARK ITEM #${{item.sparkIndex}}</span>
                      <span style="font-size:11px; color:#64748b; margin-left:6px;">Aisle ${{item.aisle}}</span>
                      <div class="title">${{item.name}}</div>
                      <div class="meta">${{item.size}} • Qty: <strong>${{item.qty}}</strong></div>
                      <div class="barcode-box">
                        <svg id="${{bcId}}" class="bc"></svg>
                        <div class="upc-num">UPC: ${{item.upc}}</div>
                      </div>
                    </div>
                  `;
                  setTimeout(() => {{
                    JsBarcode("#" + bcId, item.upc, {{format: "UPC", width: 2, height: 45, displayValue: false}});
                  }}, 50);
                }});
              }}
            }}

            function switchMode() {{
              mode = mode === 'PICK' ? 'SCAN' : 'PICK';
              render();
              window.scrollTo(0,0);
            }}

            function toggleDrawer(id) {{
              const d = document.getElementById(id);
              d.style.display = d.style.display === 'block' ? 'none' : 'block';
            }}

            render();
          </script>
        </body>
        </html>
        """

        st.components.v1.html(html_code, height=900, scrolling=True)

    except Exception as e:
        st.error(f"Error processing screenshot: {e}")
