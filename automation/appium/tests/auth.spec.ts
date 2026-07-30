import loginPage from '../pages/login.page';
import dashboardPage from '../pages/dashboard.page';

describe('Appium Mobile Authentication Suite', () => {
  it('TC_MOB_AUTH_001: Verify Mobile Email Login Flow', async () => {
    await loginPage.login('tvijay1098@gmail.com', 'CorrectPassword123');
    const isLoaded = await dashboardPage.isDashboardLoaded();
    expect(isLoaded).toBe(true);
  });

  it('TC_MOB_AUTH_002: Verify Google Sign-In Element Visibility', async () => {
    await loginPage.clickGoogleSignIn();
  });
});
