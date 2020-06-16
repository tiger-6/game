#include "cbase.h"

#include "mom_run_safeguards.h"
#include "in_buttons.h"
#include "mom_player_shared.h"

#ifdef CLIENT_DLL
#include "input.h"
#endif

#include "tier0/memdbgon.h"

#define MOM_DOUBLEPRESS_MAXTIME 0.5f

static MAKE_CONVAR(mom_run_safeguard_practicemode, "1", FCVAR_ARCHIVE | FCVAR_REPLICATED,
    "Changes the safeguard for enabling practice mode during a run.\n"
    "0 = OFF,\n"
    "1 = Enable when not pressing any movement keys,\n"
    "2 - Enable on double press.\n",
    RUN_SAFEGUARD_MODE_FIRST, RUN_SAFEGUARD_MODE_LAST);

static MAKE_CONVAR(mom_run_safeguard_restart, "1", FCVAR_ARCHIVE | FCVAR_REPLICATED,
    "Changes the safeguard for restarting the map during a run.\n"
    "0 = OFF,\n"
    "1 = Enable when not pressing any movement keys,\n"
    "2 - Enable on double press.\n",
    RUN_SAFEGUARD_MODE_FIRST, RUN_SAFEGUARD_MODE_LAST);

static MAKE_CONVAR(mom_run_safeguard_saveloc_tele, "1", FCVAR_ARCHIVE | FCVAR_REPLICATED,
    "Changes the safeguard for teleporting to a saved location during a run.\n"
    "0 = OFF,\n"
    "1 = Enable when not pressing any movement keys,\n"
    "2 - Enable on double press.\n",
    RUN_SAFEGUARD_MODE_FIRST, RUN_SAFEGUARD_MODE_LAST);

static MAKE_CONVAR(mom_run_safeguard_chat_open, "1", FCVAR_ARCHIVE | FCVAR_REPLICATED,
    "Changes the safeguard for opening chat during a run.\n"
    "0 = OFF,\n"
    "1 = Enable when not pressing any movement keys,\n"
    "2 - Enable on double press.\n",
    RUN_SAFEGUARD_MODE_FIRST, RUN_SAFEGUARD_MODE_LAST);

MomRunSafeguards::MomRunSafeguards()
    : m_pLocalPlayer(nullptr)
{
    m_arrpszAction[RUN_SAFEGUARD_PRACTICEMODE] = "enable practice mode";
    m_arrpszAction[RUN_SAFEGUARD_RESTART] = "restart map";
    m_arrpszAction[RUN_SAFEGUARD_SAVELOC_TELE] = "teleport to saveloc";
    m_arrpszAction[RUN_SAFEGUARD_CHAT_OPEN] = "open chat";

    for (int i = 0; i < RUN_SAFEGUARD_COUNT; i++)
    {
        m_szLastTimesPressed[i] = 0.0f;
        m_szDoublePressSafeguards[i] = true;
    }
}

bool MomRunSafeguards::IsSafeguarded(RunSafeguardType_t type)
{
    return IsSafeguarded(type, GetModeFromType(type));
}

bool MomRunSafeguards::IsSafeguarded(RunSafeguardType_t type, RunSafeguardMode_t mode)
{
    CMomentumPlayer *pPlayer;
#ifdef CLIENT_DLL
    pPlayer = C_MomentumPlayer::GetLocalMomPlayer();
#elif GAME_DLL
    pPlayer = CMomentumPlayer::GetLocalPlayer();
#endif
    if (!pPlayer)
        return false; 

    CMomRunEntityData *pEntData;
#ifdef CLIENT_DLL
    pEntData = pPlayer->GetCurrentUIEntData();
#elif GAME_DLL
    pEntData = pPlayer->GetRunEntData();
#endif
    if (!pEntData)
        return false;

    if (!pEntData->m_bTimerRunning || pPlayer->IsObserver())
        return false; 

    m_pLocalPlayer = pPlayer;

    switch (mode)
    {
    case RUN_SAFEGUARD_MODE_MOVEMENTKEYS:
        return IsMovementKeysSafeguarded(type);
    case RUN_SAFEGUARD_MODE_DOUBLEPRESS:
        return IsDoublePressSafeguarded(type);
    default:
        return false;
    }
}

RunSafeguardMode_t MomRunSafeguards::GetModeFromType(int type)
{
    return GetModeFromType(RunSafeguardType_t(type));
}

RunSafeguardMode_t MomRunSafeguards::GetModeFromType(RunSafeguardType_t type)
{
    switch (type)
    {
    case RUN_SAFEGUARD_PRACTICEMODE:
        return RunSafeguardMode_t(mom_run_safeguard_practicemode.GetInt());
    case RUN_SAFEGUARD_RESTART:
        return RunSafeguardMode_t(mom_run_safeguard_restart.GetInt());
    case RUN_SAFEGUARD_SAVELOC_TELE:
        return RunSafeguardMode_t(mom_run_safeguard_saveloc_tele.GetInt());
    case RUN_SAFEGUARD_CHAT_OPEN:
        return RunSafeguardMode_t(mom_run_safeguard_chat_open.GetInt());
    default:
        return RUN_SAFEGUARD_MODE_INVALID;
    }
}

void MomRunSafeguards::SetMode(int type, int mode)
{
    SetMode(RunSafeguardType_t(type), RunSafeguardMode_t(mode));
}

void MomRunSafeguards::SetMode(RunSafeguardType_t type, RunSafeguardMode_t mode)
{
    switch (type)
    {
    case RUN_SAFEGUARD_PRACTICEMODE:
        mom_run_safeguard_practicemode.SetValue(mode);
        break;
    case RUN_SAFEGUARD_RESTART:
        mom_run_safeguard_restart.SetValue(mode);
        break;
    case RUN_SAFEGUARD_SAVELOC_TELE:
        mom_run_safeguard_saveloc_tele.SetValue(mode);
        break;
    case RUN_SAFEGUARD_CHAT_OPEN:
        mom_run_safeguard_chat_open.SetValue(mode);
        break;
    }
}

bool MomRunSafeguards::IsMovementKeysSafeguarded(RunSafeguardType_t type)
{
    int nButtons = 0;
#ifdef CLIENT_DLL
    nButtons = ::input->GetButtonBits(engine->IsPlayingDemo());
#elif GAME_DLL
    nButtons = m_pLocalPlayer->m_nButtons;
#endif
    if ((nButtons & (IN_FORWARD | IN_MOVELEFT | IN_MOVERIGHT | IN_BACK | IN_JUMP | IN_DUCK | IN_WALK)) != 0)
    {
        Warning("You cannot %s when movement keys are held down while the timer is running!\n"
                "You can turn this safeguard off in the Gameplay Settings!\n", m_arrpszAction[type]);
        return true;
    }
    return false;
}

bool MomRunSafeguards::IsDoublePressSafeguarded(RunSafeguardType_t type)
{
    if (gpGlobals->curtime > m_szLastTimesPressed[type] + MOM_DOUBLEPRESS_MAXTIME)
    {
        m_szDoublePressSafeguards[type] = true;
    }
    m_szLastTimesPressed[type] = gpGlobals->curtime;
    if (m_szDoublePressSafeguards[type])
    {
        Warning("You must double press the key to %s while the timer is running!\n"
                "You can turn this safeguard off in the Gameplay Settings!\n", m_arrpszAction[type]);
        m_szDoublePressSafeguards[type] = false;
        return true;
    }
    return false;
}

static MomRunSafeguards s_RunSafeguards;
MomRunSafeguards *g_pRunSafeguards = &s_RunSafeguards;
