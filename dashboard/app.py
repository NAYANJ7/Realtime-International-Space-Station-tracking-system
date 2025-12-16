import streamlit as st
import pandas as pd
import numpy as np
import mysql.connector
from mysql.connector import pooling
import time
from datetime import datetime, timedelta
import plotly.graph_objects as go
from functools import lru_cache

# Page config
st.set_page_config(
    page_title="ISS Real-Time Tracker",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Enhanced CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {font-family: 'Inter', sans-serif !important;}
    .main {background: #0a0e1a; color: #e4e6eb;}
    .stApp {background: #0a0e1a;}
    
    h1 {
        color: #e4e6eb !important; 
        font-weight: 600 !important; 
        font-size: 2.5rem !important; 
        letter-spacing: -0.03em; 
        margin-bottom: 0.3rem !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    h2 {
        color: #c4c6d0 !important; 
        font-weight: 600 !important; 
        font-size: 1.4rem !important;
        margin-top: 2rem !important;
    }
    
    h3 {
        color: #b8bcc4 !important; 
        font-weight: 500 !important; 
        font-size: 1.1rem !important; 
        margin-top: 1.5rem !important;
    }
    
    .metric-card {
        background: linear-gradient(145deg, #1a1f2e 0%, #14182a 100%);
        border: 1px solid rgba(102, 126, 234, 0.15);
        border-radius: 16px;
        padding: 20px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    .metric-card:hover {
        border-color: rgba(102, 126, 234, 0.4);
        transform: translateY(-3px);
        box-shadow: 0 8px 16px rgba(102, 126, 234, 0.2);
    }
    
    .metric-label {
        font-size: 0.7rem; 
        color: #8b92a8; 
        font-weight: 600; 
        text-transform: uppercase; 
        letter-spacing: 0.08em; 
        margin-bottom: 8px;
    }
    .metric-value {
        font-size: 2rem; 
        color: #fff; 
        font-weight: 700; 
        letter-spacing: -0.02em;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    .metric-unit {
        font-size: 0.85rem; 
        color: #7b8199; 
        font-weight: 400; 
        margin-top: 6px;
    }
    
    .status-live {
        display: inline-flex; 
        align-items: center; 
        gap: 10px; 
        padding: 8px 18px; 
        background: rgba(34, 197, 94, 0.15); 
        border: 1.5px solid rgba(34, 197, 94, 0.4); 
        border-radius: 24px; 
        font-size: 0.85rem; 
        color: #22c55e; 
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(34, 197, 94, 0.2);
    }
    .status-dot {
        width: 8px; 
        height: 8px; 
        background: #22c55e; 
        border-radius: 50%; 
        animation: pulse-dot 2s infinite;
        box-shadow: 0 0 12px rgba(34, 197, 94, 0.8);
    }
    
    @keyframes pulse-dot {
        0%, 100% {opacity: 1; transform: scale(1);}
        50% {opacity: 0.6; transform: scale(0.9);}
    }
    
    .info-banner {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.12) 0%, rgba(118, 75, 162, 0.12) 100%);
        border-left: 4px solid rgb(102, 126, 234);
        padding: 16px 20px;
        border-radius: 8px;
        margin: 20px 0;
        font-size: 0.95rem;
        color: #c4c6d0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    
    .stat-box {
        background: rgba(26, 31, 46, 0.8);
        border: 1px solid rgba(102, 126, 234, 0.2);
        border-radius: 12px;
        padding: 18px;
        margin: 10px 0;
    }
    
    .stat-row {
        display: flex;
        justify-content: space-between;
        padding: 12px 0;
        border-bottom: 1px solid rgba(255,255,255,0.05);
    }
    
    .stat-row:last-child {
        border-bottom: none;
    }
    
    .stat-label {
        color: #8b92a8;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    .stat-value {
        color: #e4e6eb;
        font-size: 1rem;
        font-weight: 600;
    }
    
    .location-card {
        background: linear-gradient(145deg, rgba(102, 126, 234, 0.08), rgba(118, 75, 162, 0.08));
        border: 1px solid rgba(102, 126, 234, 0.25);
        border-radius: 12px;
        padding: 20px;
        margin: 16px 0;
    }
    
    .location-title {
        color: rgb(102, 126, 234);
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 12px;
    }
    
    .location-value {
        color: #fff;
        font-size: 1.8rem;
        font-weight: 700;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        margin-bottom: 8px;
    }
    
    .location-desc {
        color: #8b92a8;
        font-size: 0.85rem;
    }
    
    .orbit-info {
        background: rgba(139, 92, 246, 0.08);
        border: 1px solid rgba(139, 92, 246, 0.2);
        border-radius: 10px;
        padding: 16px;
        margin: 12px 0;
    }
    
    .orbit-info-title {
        color: rgb(139, 92, 246);
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    
    .orbit-info-text {
        color: #b8bcc4;
        font-size: 0.85rem;
        line-height: 1.6;
    }
    
    ::-webkit-scrollbar {width: 10px; height: 10px;}
    ::-webkit-scrollbar-track {background: #1a1f2e; border-radius: 5px;}
    ::-webkit-scrollbar-thumb {background: #667eea; border-radius: 5px;}
    ::-webkit-scrollbar-thumb:hover {background: #764ba2;}
    
    .divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.3), transparent);
        margin: 2.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Database connection
@st.cache_resource
def get_pool():
    return pooling.MySQLConnectionPool(
        pool_name="iss_pool",
        pool_size=5,
        pool_reset_session=False,
        host="mysql",
        user="root",
        password="password",
        database="iss_db",
        port=3306,
        autocommit=True,
        connect_timeout=5
    )

def query_db(sql):
    try:
        pool = get_pool()
        conn = pool.get_connection()
        df = pd.read_sql(sql, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"DB Error: {str(e)}")
        return pd.DataFrame()

# Data functions
@st.cache_data(ttl=1, show_spinner=False)
def get_current_position():
    sql = "SELECT * FROM iss_positions ORDER BY ts_unix DESC LIMIT 1"
    df = query_db(sql)
    return None if df.empty else df.iloc[0]

@st.cache_data(ttl=10, show_spinner=False)
def get_statistics():
    sql = """SELECT 
        COUNT(*) as total_records,
        MIN(altitude_km) as min_alt,
        MAX(altitude_km) as max_alt,
        AVG(altitude_km) as avg_alt,
        AVG(velocity_kmh) as avg_vel,
        MIN(ts_unix) as first_record,
        MAX(ts_unix) as last_record,
        STDDEV(altitude_km) as stddev_alt,
        STDDEV(velocity_kmh) as stddev_vel
    FROM iss_positions"""
    df = query_db(sql)
    return df.iloc[0] if not df.empty else None

@st.cache_data(ttl=5, show_spinner=False)
def get_recent_positions(n=50):
    sql = f"SELECT latitude, longitude, altitude_km, velocity_kmh, ts_unix FROM iss_positions ORDER BY ts_unix DESC LIMIT {n}"
    return query_db(sql)

@st.cache_data(ttl=5, show_spinner=False)
def get_hourly_stats():
    sql = """SELECT 
        DATE_FORMAT(FROM_UNIXTIME(ts_unix), '%H:00') as hour,
        COUNT(*) as record_count,
        AVG(altitude_km) as avg_altitude,
        AVG(velocity_kmh) as avg_velocity
    FROM iss_positions
    WHERE ts_unix > UNIX_TIMESTAMP() - 86400
    GROUP BY DATE_FORMAT(FROM_UNIXTIME(ts_unix), '%H:00')
    ORDER BY hour DESC
    LIMIT 24"""
    return query_db(sql)

# Utility functions
def get_country_region(lat, lon):
    """Determine approximate region"""
    regions = {
        (-90, -60): "Antarctica",
        (-60, -30): "Southern Ocean",
        (-30, 0): {
            (-180, -90): "South America",
            (-90, 20): "South America / Atlantic",
            (20, 60): "Africa / Indian Ocean",
            (60, 180): "Australia / Pacific"
        },
        (0, 30): {
            (-180, -90): "Pacific Ocean",
            (-90, -20): "Central America / Caribbean",
            (-20, 20): "Atlantic Ocean",
            (20, 60): "Africa / Middle East",
            (60, 100): "Indian Ocean",
            (100, 180): "Southeast Asia / Pacific"
        },
        (30, 60): {
            (-180, -120): "North Pacific",
            (-120, -60): "North America",
            (-60, 0): "North Atlantic",
            (0, 40): "Europe",
            (40, 80): "Central Asia",
            (80, 140): "East Asia",
            (140, 180): "North Pacific"
        },
        (60, 90): "Arctic Ocean / Northern regions"
    }
    
    for lat_range, region in regions.items():
        if lat_range[0] <= lat < lat_range[1]:
            if isinstance(region, dict):
                for lon_range, subregion in region.items():
                    if lon_range[0] <= lon < lon_range[1]:
                        return subregion
                return "Ocean"
            return region
    return "Unknown"

def calculate_orbital_period(recent_df):
    """Calculate approximate orbital period from recent data"""
    if len(recent_df) < 10:
        return 92.68  # Standard ISS orbital period
    
    # Find longitude crossings
    sorted_df = recent_df.sort_values('ts_unix')
    lon_diff = sorted_df['longitude'].diff().abs()
    
    # Detect when ISS completes significant portion of orbit
    large_jumps = lon_diff > 180  # Crossing the date line
    
    if large_jumps.sum() > 0:
        time_between = (sorted_df.iloc[-1]['ts_unix'] - sorted_df.iloc[0]['ts_unix']) / 60
        return time_between
    
    return 92.68

def create_2d_map_view(lat, lon, alt):
    """Create a clear 2D world map with satellite position using Plotly"""
    
    # Create a Plotly map instead of pydeck (more reliable)
    fig = go.Figure()
    
    # Add the satellite position as a marker
    fig.add_trace(go.Scattergeo(
        lon=[lon],
        lat=[lat],
        mode='markers+text',
        marker=dict(
            size=20,
            color='red',
            symbol='circle',
            line=dict(width=3, color='white')
        ),
        text=['🛰️ ISS'],
        textposition="top center",
        textfont=dict(size=16, color='white'),
        name='ISS Position',
        hovertemplate='<b>International Space Station</b><br>' +
                     f'Latitude: {lat:.4f}°<br>' +
                     f'Longitude: {lon:.4f}°<br>' +
                     f'Altitude: {alt:.2f} km<br>' +
                     '<extra></extra>'
    ))
    
    # Add coverage circle (approximate)
    circle_lats = []
    circle_lons = []
    for angle in range(0, 361, 10):
        # Approximate circle calculation (500 km radius)
        angle_rad = np.radians(angle)
        radius_deg = 500 / 111  # Rough conversion: 1 degree ≈ 111 km
        circle_lat = lat + radius_deg * np.sin(angle_rad)
        circle_lon = lon + radius_deg * np.cos(angle_rad) / np.cos(np.radians(lat))
        circle_lats.append(circle_lat)
        circle_lons.append(circle_lon)
    
    fig.add_trace(go.Scattergeo(
        lon=circle_lons,
        lat=circle_lats,
        mode='lines',
        line=dict(width=2, color='rgba(102, 126, 234, 0.6)'),
        fill='toself',
        fillcolor='rgba(102, 126, 234, 0.2)',
        name='Coverage Area',
        hoverinfo='skip'
    ))
    
    # Configure the map layout
    fig.update_geos(
        projection_type="natural earth",
        showland=True,
        landcolor='rgb(40, 45, 55)',
        showcountries=True,
        countrycolor='rgb(80, 90, 105)',
        showocean=True,
        oceancolor='rgb(25, 30, 40)',
        showlakes=True,
        lakecolor='rgb(25, 30, 40)',
        showcoastlines=True,
        coastlinecolor='rgb(100, 110, 125)',
        bgcolor='rgb(15, 20, 30)',
        center=dict(lat=lat, lon=lon),
        projection_scale=1.5
    )
    
    fig.update_layout(
        height=500,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor='rgb(15, 20, 30)',
        showlegend=False,
        geo=dict(
            showframe=False,
            projection_scale=1.5
        )
    )
    
    return fig

# ===================================================================
# MAIN DASHBOARD
# ===================================================================

# Header
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("<h1>🛰️ ISS Real-Time Orbital Tracker</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #8b92a8; font-size: 0.95rem; margin-top: -8px;'>Live monitoring of the International Space Station · Data Pipeline: Kafka → Spark → MySQL</p>", unsafe_allow_html=True)

with col_h2:
    st.markdown("""
        <div style='text-align: right; margin-top: 16px;'>
            <div class='status-live'><div class='status-dot'></div>LIVE</div>
        </div>
    """, unsafe_allow_html=True)

# Initialize
if 'refresh_count' not in st.session_state:
    st.session_state.refresh_count = 0

# Get data
pos = get_current_position()

if pos is None:
    st.info("⏳ Initializing ISS tracking systems...")
    time.sleep(2)
    st.rerun()

lat, lon = pos["latitude"], pos["longitude"]
alt, vel = pos["altitude_km"], pos["velocity_kmh"]
visibility = pos.get("visibility", "unknown")
timestamp = pos["ts_unix"]
current_region = get_country_region(lat, lon)

# Calculate derived metrics
distance_from_center = 6371 + alt  # Earth radius + altitude
orbital_velocity_mps = vel / 3.6
time_for_orbit = 92.68  # minutes

# ===================================================================
# PRIMARY METRICS
# ===================================================================
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-label'>Latitude</div>
            <div class='metric-value'>{lat:.4f}°</div>
            <div class='metric-unit'>{"North" if lat >= 0 else "South"} Hemisphere</div>
        </div>
    """, unsafe_allow_html=True)

with m2:
    st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-label'>Longitude</div>
            <div class='metric-value'>{lon:.4f}°</div>
            <div class='metric-unit'>{"East" if lon >= 0 else "West"} of Prime Meridian</div>
        </div>
    """, unsafe_allow_html=True)

with m3:
    st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-label'>Altitude</div>
            <div class='metric-value'>{alt:.2f}</div>
            <div class='metric-unit'>km above Earth's surface</div>
        </div>
    """, unsafe_allow_html=True)

with m4:
    vis_emoji = "☀️" if visibility == "daylight" else "🌙"
    st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-label'>Velocity</div>
            <div class='metric-value'>{vel:.0f}</div>
            <div class='metric-unit'>km/h · {vis_emoji} {visibility}</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# ===================================================================
# 2D WORLD MAP VIEW
# ===================================================================
st.markdown("<h2>🌍 Real-Time Position on World Map</h2>", unsafe_allow_html=True)

col_map, col_info = st.columns([2.5, 1])

with col_map:
    map_fig = create_2d_map_view(lat, lon, alt)
    st.plotly_chart(map_fig, use_container_width=True)
    
    st.caption("🛰️ Red marker shows current ISS position | Blue shaded area indicates visibility coverage (~500 km radius)")

with col_info:
    # Current location
    st.markdown(f"""
        <div class='location-card'>
            <div class='location-title'>📍 Current Location</div>
            <div class='location-value'>{current_region}</div>
            <div class='location-desc'>
                {abs(lat):.2f}° {"N" if lat >= 0 else "S"}, 
                {abs(lon):.2f}° {"E" if lon >= 0 else "W"}
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Orbital statistics
    stats = get_statistics()
    if stats is not None:
        uptime_min = (stats["last_record"] - stats["first_record"]) / 60
        orbits_completed = uptime_min / time_for_orbit
        
        st.markdown(f"""
            <div class='stat-box'>
                <div class='stat-row'>
                    <span class='stat-label'>⏱️ System Uptime</span>
                    <span class='stat-value'>{uptime_min:.1f} min</span>
                </div>
                <div class='stat-row'>
                    <span class='stat-label'>🔄 Orbits Completed</span>
                    <span class='stat-value'>{orbits_completed:.2f}</span>
                </div>
                <div class='stat-row'>
                    <span class='stat-label'>📊 Data Points</span>
                    <span class='stat-value'>{stats['total_records']:,}</span>
                </div>
                <div class='stat-row'>
                    <span class='stat-label'>🌍 Ground Track</span>
                    <span class='stat-value'>{orbits_completed * 40075:.0f} km</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # Orbital mechanics info
    st.markdown(f"""
        <div class='orbit-info'>
            <div class='orbit-info-title'>⚡ Speed Stats</div>
            <div class='orbit-info-text'>
                <strong>{orbital_velocity_mps:.0f} m/s</strong> orbital velocity<br>
                <strong>28× faster</strong> than speed of sound<br>
                <strong>8 km/s</strong> relative to Earth's surface
            </div>
        </div>
    """, unsafe_allow_html=True)

# Info banner
st.markdown(f"""
    <div class='info-banner'>
        <strong>🔍 Live Status:</strong> ISS is currently over <strong>{current_region}</strong> at an altitude of 
        <strong>{alt:.1f} km</strong>, traveling at <strong>{vel:,.0f} km/h</strong>. 
        At this speed, the ISS completes one full orbit around Earth approximately every <strong>92 minutes</strong>.
    </div>
""", unsafe_allow_html=True)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# ===================================================================
# DETAILED ANALYTICS
# ===================================================================
st.markdown("<h2>📊 Orbital Analytics & Performance</h2>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📈 Altitude & Velocity", "⏱️ Hourly Statistics", "🎯 Data Quality"])

with tab1:
    recent_df = get_recent_positions(100)
    
    if not recent_df.empty:
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            # Altitude chart
            fig_alt = go.Figure()
            fig_alt.add_trace(go.Scatter(
                x=list(range(len(recent_df))),
                y=recent_df['altitude_km'],
                mode='lines+markers',
                name='Altitude',
                line=dict(color='rgb(102, 126, 234)', width=3),
                marker=dict(size=5, color='rgb(102, 126, 234)'),
                fill='tozeroy',
                fillcolor='rgba(102, 126, 234, 0.2)'
            ))
            fig_alt.update_layout(
                title="Altitude Over Last 100 Data Points",
                xaxis_title="Data Point",
                yaxis_title="Altitude (km)",
                template="plotly_dark",
                height=300,
                paper_bgcolor='rgba(26, 31, 46, 0.6)',
                plot_bgcolor='rgba(0,0,0,0)',
            )
            st.plotly_chart(fig_alt, use_container_width=True)
        
        with col_chart2:
            # Velocity chart
            fig_vel = go.Figure()
            fig_vel.add_trace(go.Scatter(
                x=list(range(len(recent_df))),
                y=recent_df['velocity_kmh'],
                mode='lines+markers',
                name='Velocity',
                line=dict(color='rgb(34, 197, 94)', width=3),
                marker=dict(size=5, color='rgb(34, 197, 94)'),
                fill='tozeroy',
                fillcolor='rgba(34, 197, 94, 0.2)'
            ))
            fig_vel.update_layout(
                title="Velocity Over Last 100 Data Points",
                xaxis_title="Data Point",
                yaxis_title="Velocity (km/h)",
                template="plotly_dark",
                height=300,
                paper_bgcolor='rgba(26, 31, 46, 0.6)',
                plot_bgcolor='rgba(0,0,0,0)',
            )
            st.plotly_chart(fig_vel, use_container_width=True)

with tab2:
    hourly_df = get_hourly_stats()
    
    if not hourly_df.empty:
        # Hourly record count
        fig_hourly = go.Figure()
        fig_hourly.add_trace(go.Bar(
            x=hourly_df['hour'],
            y=hourly_df['record_count'],
            name='Records',
            marker=dict(color='rgb(139, 92, 246)'),
        ))
        fig_hourly.update_layout(
            title="Data Ingestion Rate by Hour (Last 24h)",
            xaxis_title="Hour",
            yaxis_title="Record Count",
            template="plotly_dark",
            height=350,
            paper_bgcolor='rgba(26, 31, 46, 0.6)',
            plot_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig_hourly, use_container_width=True)
        
        st.caption(f"📊 Total records in last 24h: {hourly_df['record_count'].sum():,} | Avg per hour: {hourly_df['record_count'].mean():.0f}")

with tab3:
    if stats is not None:
        col_q1, col_q2, col_q3 = st.columns(3)
        
        with col_q1:
            st.markdown(f"""
                <div class='location-card'>
                    <div class='location-title'>Altitude Range</div>
                    <div class='location-value'>{stats['min_alt']:.2f} - {stats['max_alt']:.2f}</div>
                    <div class='location-desc'>Min - Max (km)</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col_q2:
            alt_stability = "Stable" if stats['stddev_alt'] < 1 else "Variable"
            st.markdown(f"""
                <div class='location-card'>
                    <div class='location-title'>Altitude Stability</div>
                    <div class='location-value'>{alt_stability}</div>
                    <div class='location-desc'>StdDev: {stats['stddev_alt']:.4f} km</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col_q3:
            vel_stability = "Stable" if stats['stddev_vel'] < 50 else "Variable"
            st.markdown(f"""
                <div class='location-card'>
                    <div class='location-title'>Velocity Stability</div>
                    <div class='location-value'>{vel_stability}</div>
                    <div class='location-desc'>StdDev: {stats['stddev_vel']:.2f} km/h</div>
                </div>
            """, unsafe_allow_html=True)

# Auto-refresh
time.sleep(2)
st.session_state.refresh_count += 1
st.rerun()