import { create } from 'zustand';

// Process state types
export interface Alarm {
  level: 'HIGH' | 'MEDIUM' | 'LOW';
  message: string;
  tag: string;
  timestamp?: number;
  acknowledged?: boolean;
}

export interface ProcessState {
  timestamp: number;
  
  // Tank Levels (%)
  intake_level: number;
  flash_mix_level: number;
  floc_level: number;
  sed_level: number;
  chlorine_contact_level: number;
  clearwell_level: number;
  
  // Pump States
  pump_p101_running: boolean;
  pump_p101_speed: number;
  pump_p102_running: boolean;
  pump_p102_speed: number;
  pump_p201_running: boolean;
  pump_p201_speed: number;
  pump_p202_running: boolean;
  pump_p202_speed: number;
  pump_p301_running: boolean;
  pump_p301_speed: number;
  pump_p302_running: boolean;
  pump_p302_speed: number;
  
  // Valve Positions
  valve_v101: number;
  valve_v102: number;
  valve_v103: number;
  valve_v104: number;
  valve_v105: number;
  
  // Chemical Dosing
  chlorine_dose: number;
  chlorine_flow: number;
  alum_dose: number;
  alum_flow: number;
  fluoride_dose: number;
  fluoride_flow: number;
  
  // Water Quality
  raw_turbidity: number;
  filtered_turbidity: number;
  ph_raw: number;
  ph_treated: number;
  chlorine_residual: number;
  temperature: number;
  conductivity: number;
  
  // Flow Rates
  raw_water_flow: number;
  treated_flow: number;
  distribution_flow: number;
  backwash_flow: number;
  
  // Pressures
  intake_pressure: number;
  filter_inlet_pressure: number;
  filter_outlet_pressure: number;
  distribution_pressure: number;
  
  // Filter Status
  filter_1_status: string;
  filter_1_runtime: number;
  filter_2_status: string;
  filter_2_runtime: number;
  filter_dp: number;
  
  // Alarms
  alarms: Alarm[];
}

interface ProcessStore {
  // Current state
  state: ProcessState | null;
  isConnected: boolean;
  lastUpdate: number | null;
  
  // Historical data for trends
  history: {
    timestamps: number[];
    clearwell_level: number[];
    distribution_pressure: number[];
    chlorine_residual: number[];
    ph_treated: number[];
    raw_water_flow: number[];
    distribution_flow: number[];
  };
  
  // Actions
  updateState: (newState: ProcessState) => void;
  setConnected: (connected: boolean) => void;
  addToHistory: (state: ProcessState) => void;
  acknowledgeAlarm: (tag: string) => void;
}

const MAX_HISTORY_POINTS = 300; // ~5 minutes at 1 second updates

export const useProcessStore = create<ProcessStore>((set, get) => ({
  state: null,
  isConnected: false,
  lastUpdate: null,
  
  history: {
    timestamps: [],
    clearwell_level: [],
    distribution_pressure: [],
    chlorine_residual: [],
    ph_treated: [],
    raw_water_flow: [],
    distribution_flow: [],
  },
  
  updateState: (newState: ProcessState) => {
    set({ 
      state: newState, 
      lastUpdate: Date.now() 
    });
    get().addToHistory(newState);
  },
  
  setConnected: (connected: boolean) => {
    set({ isConnected: connected });
  },
  
  addToHistory: (state: ProcessState) => {
    set((prev) => {
      const history = { ...prev.history };
      
      // Add new data points
      history.timestamps.push(state.timestamp * 1000);
      history.clearwell_level.push(state.clearwell_level);
      history.distribution_pressure.push(state.distribution_pressure);
      history.chlorine_residual.push(state.chlorine_residual);
      history.ph_treated.push(state.ph_treated);
      history.raw_water_flow.push(state.raw_water_flow);
      history.distribution_flow.push(state.distribution_flow);
      
      // Trim to max points
      if (history.timestamps.length > MAX_HISTORY_POINTS) {
        history.timestamps = history.timestamps.slice(-MAX_HISTORY_POINTS);
        history.clearwell_level = history.clearwell_level.slice(-MAX_HISTORY_POINTS);
        history.distribution_pressure = history.distribution_pressure.slice(-MAX_HISTORY_POINTS);
        history.chlorine_residual = history.chlorine_residual.slice(-MAX_HISTORY_POINTS);
        history.ph_treated = history.ph_treated.slice(-MAX_HISTORY_POINTS);
        history.raw_water_flow = history.raw_water_flow.slice(-MAX_HISTORY_POINTS);
        history.distribution_flow = history.distribution_flow.slice(-MAX_HISTORY_POINTS);
      }
      
      return { history };
    });
  },
  
  acknowledgeAlarm: (tag: string) => {
    set((prev) => {
      if (!prev.state) return prev;
      
      const alarms = prev.state.alarms.map((alarm) =>
        alarm.tag === tag ? { ...alarm, acknowledged: true } : alarm
      );
      
      return {
        state: { ...prev.state, alarms },
      };
    });
  },
}));


// UI Store for dashboard settings
interface UIStore {
  darkMode: boolean;
  selectedTab: string;
  showAlarmPanel: boolean;
  
  setDarkMode: (dark: boolean) => void;
  setSelectedTab: (tab: string) => void;
  setShowAlarmPanel: (show: boolean) => void;
}

export const useUIStore = create<UIStore>((set) => ({
  darkMode: true,
  selectedTab: 'overview',
  showAlarmPanel: true,
  
  setDarkMode: (darkMode) => set({ darkMode }),
  setSelectedTab: (selectedTab) => set({ selectedTab }),
  setShowAlarmPanel: (showAlarmPanel) => set({ showAlarmPanel }),
}));
