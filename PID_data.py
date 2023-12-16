class PID_data:
    _Throttle: (int, int, int, int, int)

    _PID_Ro_Kp: float
    _PID_Ro_Ki: float
    _PID_Ro_Kd: float
    _PID_Ro_ref: int
    _PID_Ro_meas: float
    _PID_Ro_out: float

    _PID_Ri_Kp: float
    _PID_Ri_Ki: float
    _PID_Ri_Kd: float
    _PID_Ri_ref: float
    _PID_Ri_meas: float
    _PID_Ri_out: int

    _PID_Po_Kp: float
    _PID_Po_Ki: float
    _PID_Po_Kd: float
    _PID_Po_ref: int
    _PID_Po_meas: float
    _PID_Po_out: float

    _PID_Pi_Kp: float
    _PID_Pi_Ki: float
    _PID_Pi_Kd: float
    _PID_Pi_ref: float
    _PID_Pi_meas: float
    _PID_Pi_out: int

    _PID_Y_Kp: float
    _PID_Y_Ki: float
    _PID_Y_Kd: float
    _PID_Y_ref: int
    _PID_Y_meas: float
    _PID_Y_out: int

    _PID_T_Kp: float
    _PID_T_Ki: float
    _PID_T_Kd: float
    _PID_T_ref: int
    _PID_T_meas: float
    _PID_T_out: int

    def __init__(self):
        self._Throttle = (0, 0, 0, 0, 0)

        self._PID_Ro_Kp = 0.0
        self._PID_Ro_Ki = 0.0
        self._PID_Ro_Kd = 0.0
        self._PID_Ro_ref = 0
        self._PID_Ro_meas = 0.0
        self._PID_Ro_out = 0.0

        self._PID_Ri_Kp = 0.0
        self._PID_Ri_Ki = 0.0
        self._PID_Ri_Kd = 0.0
        self._PID_Ri_ref = 0.0
        self._PID_Ri_meas = 0.0
        self._PID_Ri_out = 0

        self._PID_Po_Kp = 0.0
        self._PID_Po_Ki = 0.0
        self._PID_Po_Kd = 0.0
        self._PID_Po_ref = 0
        self._PID_Po_meas = 0.0
        self._PID_Po_out = 0.0

        self._PID_Pi_Kp = 0.0
        self._PID_Pi_Ki = 0.0
        self._PID_Pi_Kd = 0.0
        self._PID_Pi_ref = 0.0
        self._PID_Pi_meas = 0.0
        self._PID_Pi_out = 0

        self._PID_Y_Kp = 0.0
        self._PID_Y_Ki = 0.0
        self._PID_Y_Kd = 0.0
        self._PID_Y_ref = 0
        self._PID_Y_meas = 0.0
        self._PID_Y_out = 0

        self._PID_T_Kp = 0.0
        self._PID_T_Ki = 0.0
        self._PID_T_Kd = 0.0
        self._PID_T_ref = 0
        self._PID_T_meas = 0.0
        self._PID_T_out = 0

    @property
    def Throttle(self):
        return self._Throttle

    @Throttle.setter
    def Throttle(self, value):
        self._Throttle = value

    @property
    def stored_gains(self):
        return [
            self._PID_Ro_Kp, self._PID_Ro_Ki, self._PID_Ro_Kd,
            self._PID_Ri_Kp, self._PID_Ri_Ki, self._PID_Ri_Kd,
            self._PID_Po_Kp, self._PID_Po_Ki, self._PID_Po_Kd,
            self._PID_Pi_Kp, self._PID_Pi_Ki, self._PID_Pi_Kd,
            self._PID_Y_Kp, self._PID_Y_Ki, self._PID_Y_Kd,
            self._PID_T_Kp, self._PID_T_Ki, self._PID_T_Kd
        ]

    @stored_gains.setter
    def stored_gains(self, values):
        self._PID_Ro_Kp, self._PID_Ro_Ki, self._PID_Ro_Kd, \
            self._PID_Ri_Kp, self._PID_Ri_Ki, self._PID_Ri_Kd, \
            self._PID_Po_Kp, self._PID_Po_Ki, self._PID_Po_Kd, \
            self._PID_Pi_Kp, self._PID_Pi_Ki, self._PID_Pi_Kd, \
            self._PID_Y_Kp, self._PID_Y_Ki, self._PID_Y_Kd, \
            self._PID_T_Kp, self._PID_T_Ki, self._PID_T_Kd = values

    @property
    def stored_plot_data(self):
        return [
            self._PID_Ro_ref, self._PID_Ro_meas, self._PID_Ro_out,
            self._PID_Ri_ref, self._PID_Ri_meas, self._PID_Ri_out,
            self._PID_Po_ref, self._PID_Po_meas, self._PID_Po_out,
            self._PID_Pi_ref, self._PID_Pi_meas, self._PID_Pi_out,
            self._PID_Y_ref, self._PID_Y_meas, self._PID_Y_out,
            self._PID_T_ref, self._PID_T_meas, self._PID_T_out
        ]

    @stored_plot_data.setter
    def stored_plot_data(self, values):
        self._PID_Ro_ref, self._PID_Ro_meas, self._PID_Ro_out, \
            self._PID_Ri_ref, self._PID_Ri_meas, self._PID_Ri_out, \
            self._PID_Po_ref, self._PID_Po_meas, self._PID_Po_out, \
            self._PID_Pi_ref, self._PID_Pi_meas, self._PID_Pi_out, \
            self._PID_Y_ref, self._PID_Y_meas, self._PID_Y_out, \
            self._PID_T_ref, self._PID_T_meas, self._PID_T_out = values