#pragma once

#include "SettingsPanel.h"

class GameplaySettingsPanel : public SettingsPanel
{
public:
    DECLARE_CLASS_SIMPLE(GameplaySettingsPanel, SettingsPanel);

    GameplaySettingsPanel(Panel *pParent, vgui::Button *pAssociate);

    void OnPageShow() override;

    void OnCheckboxChecked(Panel *panel) override;

    void OnTextChanged(Panel *pPanel, const char *pszText) override;

private:
    // General gameplay settings
    vgui::CvarToggleCheckButton *m_pEnableDevConsole;
    vgui::CvarToggleCheckButton *m_pHudFastSwitch;
    vgui::CvarToggleCheckButton *m_pOverlappingKeys;
    vgui::CvarToggleCheckButton *m_pReleaseForwardOnJump;

    vgui::CvarToggleCheckButton *m_pPlayBlockSound;
    vgui::CvarToggleCheckButton *m_pSaveCheckpoints;
    vgui::CvarSlider *m_pYawSpeedSlider;
    vgui::CvarTextEntry *m_pYawSpeedEntry;

    vgui::ComboBox *m_pRunSafeguardTypes;
    vgui::ComboBox *m_pRunSafeguardModes;

    // Gamemode
    vgui::CvarToggleCheckButton *m_pRJEnableTrailParticle, *m_pRJEnableExplosionParticle, *m_pRJEnableShootSound,
        *m_pRJToggleRocketTrailSound, *m_pRJToggleRocketExplosionSound, *m_pRJToggleRocketDecals,
        *m_pRJEnableCenterFire;

    vgui::CvarTextEntry *m_pRJRocketDrawDelayEntry;

    vgui::CvarToggleCheckButton *m_pSJEnableTrailParticle, *m_pSJEnableExplosionParticle, *m_pSJToggleStickybombDecals,
                                *m_pSJEnableExplosionSound, *m_pSJEnableDetonateSuccessSound, *m_pSJEnableDetonateFailSound,
                                *m_pSJEnableChargeSound, *m_pSJEnableChargeMeter, *m_pSJEnableStickyCounter, *m_pSJStickyCounterAutohide;

    vgui::CvarComboBox *m_pSJChargeMeterUnits;

    vgui::CvarTextEntry *m_pSJStickyDrawDelayEntry;
};