class TradingConfig:
    # Shadow Trading Targets (absolute price moves on 0-1 token scale)
    SHADOW_TP_DELTA = 0.04
    SHADOW_SL_DELTA = 0.03
    SHADOW_WINDOW_MINUTES = 60

    # Paper Trading ROI Targets
    PAPER_TP_ROI = 0.25
    PAPER_TRAILING_STOP = 0.08

    # Thresholds
    VETO_EV_THRESHOLD = 0.005
    MIN_CONVICTION_FOR_READY = 0.85
    CALIBRATION_BIAS_THRESHOLD = 20.0
