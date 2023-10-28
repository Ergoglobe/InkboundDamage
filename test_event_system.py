import event_system


def test_es():
    line = "0T22:55:51 78 I [EventSystem] broadcasting EventOnUnitDamaged-WorldStateChangeDamageUnit-TargetUnitHandle:(EntityHandle:58)-SourceEntityHandle:(EntityHandle:15)-TargetUnitTeam:Enemy-IsInActiveCombat:True-DamageAmount:178 I [EventSystem] broadcasting EventOnUnitStatusEffectAction-WorldStateChangeUnitStatusEffectAction-UnitEntityHandle:(EntityHandle:58)-ContextTargetUnitEntityHandle:(EntityHandle:58)-StatusEffect:Threaded_StatusEffect-2rURTBRv-ProcType:OnStatusInstanceRemoved-SkipPause:False"
    es = event_system.EventSystem(line)

    print(es.TargetUnitHandle)
