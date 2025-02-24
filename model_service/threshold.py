import ee

from lk_metric import compute_Lk

def threshold_optimization(magnitude, class_t1, class_t2, roi, scale, step_coarse=0.1, step_fine=0.01, tolerance=1e-3, max_iterations=10):
    """
    Optimize the threshold to maximize the Lk metric.
    """
    vmin = magnitude.reduceRegion(ee.Reducer.min(), roi, scale).values().get(0).getInfo()
    vmax = magnitude.reduceRegion(ee.Reducer.max(), roi, scale).values().get(0).getInfo()
    best_threshold = vmin
    best_Lk = -9999.0

    iteration = 0
    improved = True

    while iteration < max_iterations and improved:
        iteration += 1
        improved = False
        coarse_candidates = ee.List.sequence(vmin, vmax, step_coarse)
        local_best_thr = best_threshold
        local_best_Lk = best_Lk

        def coarse_step(T):
            Lk_current = compute_Lk(magnitude, class_t1, class_t2, T, roi, scale)
            return ee.Algorithms.If(Lk_current.gt(local_best_Lk), [Lk_current, T], [local_best_Lk, local_best_thr])
        coarse_results = coarse_candidates.map(coarse_step)
        coarse_results = ee.List(coarse_results).getInfo()
        local_best_Lk, local_best_thr = max(coarse_results)

        if local_best_Lk - best_Lk > tolerance:
            best_Lk = local_best_Lk
            best_threshold = local_best_thr
            improved = True

        low_bound = max(best_threshold - step_coarse, vmin)
        high_bound = min(best_threshold + step_coarse, vmax)
        fine_candidates = ee.List.sequence(low_bound, high_bound, step_fine)

        def fine_step(T):
            Lk_current = compute_Lk(magnitude, class_t1, class_t2, T, roi, scale)
            return ee.Algorithms.If(Lk_current.gt(local_best_Lk), [Lk_current, T], [local_best_Lk, local_best_thr])
        fine_results = fine_candidates.map(fine_step)
        fine_results = ee.List(fine_results).getInfo()
        local_best_Lk, local_best_thr = max(fine_results)

        if local_best_Lk - best_Lk > tolerance:
            best_Lk = local_best_Lk
            best_threshold = local_best_thr
            improved = True

    return best_threshold, best_Lk
