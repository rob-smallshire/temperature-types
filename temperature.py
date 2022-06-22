import operator

ABSOLUTE_ZERO = 0

class Temperature:

    _scale_classes = {}
    _promotion_rules = {}

    @classmethod
    def __init_subclass__(cls, **kwargs):
        cls._scale_classes[cls.name()] = cls
        super().__init_subclass__(**kwargs)
    
    @classmethod
    def name(cls):
        return cls.__name__.lower()
    
    @classmethod
    def promote_rule(cls, lhs_cls, rhs_cls, result_cls):
        cls._promotion_rules[frozenset((lhs_cls, rhs_cls))] = result_cls
    
    @classmethod
    def from_kelvin(cls, kelvin):
        value = cls._m * kelvin + cls._c
        return cls(value)
    
    def __init__(self, value):
        kelvin = (value - self._c) / self._m
        
        if kelvin < ABSOLUTE_ZERO:
            raise ValueError(f"Temperature {kelvin} K is below {ABSOLUTE_ZERO} K")
        
        self._kelvin = kelvin
    
    @property
    def value(self):
        return self._m * self._kelvin + self._c
        
    @property
    def symbol(self):
        return self._symbol
        
    def __getattr__(self, name):
        if name not in self._scale_classes:
            raise AttributeError(f"{type(self)} object has not attribute {name!r}")
        
        cls = self._scale_classes[name]
        
        value = cls._m * self._kelvin + cls._c
        return cls(value)
    
    def __repr__(self):
        name = type(self).__name__
        return f"{name}({self.value})"
    
    def __str__(self):
        return f"{self.value} {self.symbol}"

    @classmethod
    def _op(cls, op, lhs, rhs):
        result_cls = cls._result_type(lhs, rhs)
        result = result_cls.from_kelvin(op(lhs.kelvin.value, rhs.kelvin.value))
        return result

    @classmethod   
    def _delta_op(cls, op, lhs, rhs):
        result_cls = cls._result_type(lhs, rhs).Delta
        result = result_cls.from_kelvin(op(lhs.kelvin.value, rhs.kelvin.value))
        return result  

    @classmethod
    def _result_type(cls, lhs, rhs):
        lhs_cls = _base_type(lhs)
        rhs_cls = _base_type(rhs)
        key = frozenset((lhs_cls, rhs_cls))
        if key in cls._promotion_rules:
            result_cls = cls._promotion_rules[key]
        else:
            result_cls = lhs_cls
        return result_cls

    def __add__(self, rhs):
        if not isinstance(rhs, TemperatureDelta):
            return NotImplemented
        return self._op(operator.add, self, rhs)
    
    def __sub__(self, rhs):
        if isinstance(rhs, TemperatureDelta):
            return self._op(operator.sub, self, rhs)
        elif isinstance(rhs, Temperature):
            return self._delta_op(operator.sub, self, rhs)
        else:
            return NotImplemented
        

def _base_type(obj):
    if isinstance(obj, Temperature):
        return type(obj)
    elif isinstance(obj, TemperatureDelta):
        return obj._T
    raise TypeError(f"{obj!r} is neither a {Temperature.__name__} not a {TemperatureDelta.__name__}")

    
class TemperatureDelta:
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

    @classmethod
    def from_kelvin(cls, kelvin):
        value = cls._T._m * kelvin
        return cls(value)

    def __init__(self, value):
        self._kelvin = value / self._T._m
        
    @property
    def value(self):
        return self._T._m * self._kelvin
    
    def __getattr__(self, name):
        if name not in self._T._scale_classes:
            raise AttributeError(f"{type(self)} object has not attribute {name!r}")
        
        cls = self._T._scale_classes[name].Delta
        
        value = cls._T._m * self._kelvin
        return cls(value)
    
    def __repr__(self):
        t_name = type(self)._T.__name__
        d_name = type(self).__name__
        return f"{t_name}.{d_name}({self.value})"


def temperature_type(name, m, c, symbol):
    D = type("Delta", (TemperatureDelta,), dict())
    T = type(name, (Temperature,), dict(Delta=D, _m=m, _c=c, _symbol=symbol))
    D._T = T
    return T



Kelvin = temperature_type("Kelvin", m=1, c=0, symbol="K")
Celsius = temperature_type("Celsius", m=1, c=-273.15, symbol="°C")
Fahrenheit = temperature_type("Fahrenheit", m=9/5, c=-459.67, symbol="°F")
Rankine = temperature_type("Rankine", m=9/5, c=0, symbol="°R")

Temperature.promote_rule(Kelvin, Celsius, Kelvin)
Temperature.promote_rule(Fahrenheit, Celsius, Celsius)
Temperature.promote_rule(Fahrenheit, Kelvin, Kelvin)


if __name__ == "__main__":
    k = Celsius(5) + Kelvin.Delta(2)
    print(k)
    r = k.rankine
    print(r)