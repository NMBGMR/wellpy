Stored Procedures
---------------------

GetPointIDsPython
  **parameters:** None

  **returns:** PointID, DateInstalled, SerialNumber

GetWaterLevelsPython
  **parameters:** PointID *str*, DateMeasuredStart *datetime = null*, DateMeasuredEnd *datetime = null*

  **returns:** WellID *str*, PointID *str*, DateMeasured *datetime*, DepthToWaterBGS *float*, LevelStatus *bool?*

GetWaterLevelsContinuousPython
  **parameters:** PointID *str*, DateMeasuredStart *datetime = null*, DateMeasuredEnd *datetime = null*, QCed *bit =
  null*

  **returns:** WellID *str*, PointID *str*, WaterHead *float*, WaterHeadAdjusted *float*, DepthToWaterBGS *float*,
  DateMeasured
  *datetime*
