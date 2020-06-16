#pragma once

#ifdef CLIENT_DLL
class C_MomentumPlayer;
#elif GAME_DLL
class CMomentumPlayer;
#endif

enum RunSafeguardType_t
{
    RUN_SAFEGUARD_PRACTICEMODE = 0,
    RUN_SAFEGUARD_RESTART,
    RUN_SAFEGUARD_SAVELOC_TELE,
    RUN_SAFEGUARD_CHAT_OPEN,

    RUN_SAFEGUARD_COUNT,

    RUN_SAFEGUARD_INVALID = -1
};

enum RunSafeguardMode_t
{
    RUN_SAFEGUARD_MODE_NONE = 0,
    RUN_SAFEGUARD_MODE_MOVEMENTKEYS,
    RUN_SAFEGUARD_MODE_DOUBLEPRESS,

    RUN_SAFEGUARD_MODE_COUNT,

    RUN_SAFEGUARD_MODE_FIRST = RUN_SAFEGUARD_MODE_NONE,
    RUN_SAFEGUARD_MODE_LAST = RUN_SAFEGUARD_MODE_DOUBLEPRESS,
    RUN_SAFEGUARD_MODE_INVALID = -1
};

class MomRunSafeguards
{
  public:
    MomRunSafeguards();

    bool IsSafeguarded(RunSafeguardType_t type);
    bool IsSafeguarded(RunSafeguardType_t type, RunSafeguardMode_t mode);

    RunSafeguardMode_t GetModeFromType(int type);
    RunSafeguardMode_t GetModeFromType(RunSafeguardType_t type);

    void SetMode(int type, int mode);
    void SetMode(RunSafeguardType_t type, RunSafeguardMode_t mode);

  private:
    bool IsMovementKeysSafeguarded(RunSafeguardType_t type);
    bool IsDoublePressSafeguarded(RunSafeguardType_t type);

#ifdef CLIENT_DLL
    C_MomentumPlayer *m_pLocalPlayer;
#elif GAME_DLL
    CMomentumPlayer *m_pLocalPlayer;
#endif

    char *m_arrpszAction[RUN_SAFEGUARD_COUNT];

    float m_szLastTimesPressed[RUN_SAFEGUARD_COUNT];

    bool m_szDoublePressSafeguards[RUN_SAFEGUARD_COUNT];
};

extern MomRunSafeguards *g_pRunSafeguards;
