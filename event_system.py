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
            self.ActionData = self.clean_action_data(re_eventsystem.group("ActionData"))
            self.AbilityData = re_eventsystem.group("AbilityData")
            self.StatusEffectData = re_eventsystem.group("StatusEffectData")
            self.LootableData = re_eventsystem.group("LootableData")

    def clean_action_data(self, action_data) -> str:
        # remove _Action until end of line, dont care about the code in the parenthesis
        # eg Spiked_Action (9KqJ7Ihe)
        action_data = re.sub("_Action.*?$", "", action_data)
        # remove _Damage
        action_data = re.sub("_Damage", "", action_data)
        # replace _Legendary_ with ->
        # eg Stitch_Legendary_Splice becomes Stitch->Splice
        action_data = re.sub("_Legendary_", "->", action_data)
        # remove upgrade if it exists
        # eg ConstrictUpgrade->Entwine becomes Constrict->Entwine
        action_data = re.sub("Upgrade", "", action_data)

        return action_data
