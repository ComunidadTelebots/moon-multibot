const clamp01 = value => Math.max(0, Math.min(1, Number(value) || 0));

export function createOperationCinematics(options = {}) {
  const duration = Math.max(600, Number(options.duration) || 3200);
  let operation = null;

  const snapshot = now => {
    if (!operation) return { active: false, progress: 0, phase: "idle" };
    const progress = clamp01((Number(now) - operation.startedAt) / duration);
    const phase = progress < .24 ? "align" : progress < .76 ? "lift" : progress < 1 ? "secure" : "complete";
    return { ...operation, active: progress < 1, progress, phase };
  };

  const start = ({ now = 0, pallet = null, tool = "palletJack" } = {}) => {
    if (operation) return snapshot(now);
    operation = { startedAt: Number(now) || 0, pallet, tool };
    return snapshot(now);
  };

  const update = now => {
    const frame = snapshot(now);
    if (operation && !frame.active) operation = null;
    return frame;
  };

  const cancel = () => { operation = null; };
  return { start, update, cancel, snapshot, get active() { return Boolean(operation); } };
}
