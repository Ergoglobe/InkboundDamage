import re
import logging


class EventSystem:
    Timestamp: str
    EventOn: str
    WorldState: str
    TargetUnitHandle: int
    SourceEntityHandle: int
    TargetUnitTeam: str  # can ignore
    IsInActiveCombat: bool  # can ignore
    DamageAmount: int
    IsCriticalHit: bool
    WasDodged: bool
    ActionData: str  # janky
    AbilityData: str
    StatusEffectData: str
    LootableData: str  # can ignore ( for now? )

    def __init__(self, line):
        re_eventsystem = re.search(
            r"(?P<Timestamp>.*?)( (\d\d) I \[EventSystem\] broadcasting EventOn)(?P<EventOn>.*?)(-WorldState)(?P<WorldState>.*?)(-TargetUnitHandle:\(EntityHandle:)(?P<TargetUnitHandle>\d*)(\)-SourceEntityHandle:\(EntityHandle:)(?P<SourceEntityHandle>\d*)(\)-TargetUnitTeam:)(?P<TargetUnitTeam>.*?)(-IsInActiveCombat:)(?P<IsInActiveCombat>.*?)(-DamageAmount:)(?P<DamageAmount>\d*?)(-IsCriticalHit:)(?P<IsCriticalHit>.*?)(-WasDodged:)(?P<WasDodged>.*?)(-ActionData:ActionData-)(?P<ActionData>.*?)(-AbilityData:)(?P<AbilityData>.*?)(-StatusEffectData:)(?P<StatusEffectData>.*?)(-LootableData:)(?P<LootableData>.*?)$",
            line,
        )

        if re_eventsystem is None:
            logging.info("re_eventsystem: %s", line)
        else:
            self.Timestamp = re_eventsystem.group("Timestamp")
            self.EventOn = re_eventsystem.group("EventOn")
            self.WorldState = re_eventsystem.group("WorldState")
            self.TargetUnitHandle = re_eventsystem.group("TargetUnitHandle")
            self.SourceEntityHandle = re_eventsystem.group("SourceEntityHandle")
            self.TargetUnitTeam = re_eventsystem.group("TargetUnitTeam")
            self.IsInActiveCombat = re_eventsystem.group("IsInActiveCombat")
            self.DamageAmount = re_eventsystem.group("DamageAmount")
            self.IsCriticalHit = re_eventsystem.group("IsCriticalHit")
            self.WasDodged = re_eventsystem.group("WasDodged")
            self.ActionData = re_eventsystem.group("ActionData")
            self.AbilityData = re_eventsystem.group("AbilityData")
            self.StatusEffectData = re_eventsystem.group("StatusEffectData")
            self.LootableData = re_eventsystem.group("LootableData")
