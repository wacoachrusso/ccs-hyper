document.addEventListener('DOMContentLoaded', () => {
    const appRoot = document.getElementById('app-root');
    const appLoading = document.getElementById('app-loading');
    const { supabase } = window.supabaseClient;

    const showLoading = (isLoading) => {
        appLoading.style.display = isLoading ? 'block' : 'none';
        appRoot.style.display = isLoading ? 'none' : 'block';
    };

    const renderLoginForm = () => {
        appRoot.innerHTML = `
            <h2>Login to CCS Hyper</h2>
            <form id="login-form">
                <div class="form-group">
                    <label for="email">Email</label>
                    <input type="email" id="email" class="form-control" required>
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" class="form-control" required>
                </div>
                <button type="submit" class="btn btn-primary">Login</button>
            </form>
            <p>Or <a href="#" id="show-signup">create an account</a>.</p>
        `;
        document.getElementById('login-form').addEventListener('submit', handleLogin);
        document.getElementById('show-signup').addEventListener('click', (e) => { e.preventDefault(); renderSignupForm(); });
    };

    const renderSignupForm = () => {
        appRoot.innerHTML = `
            <h2>Create Account</h2>
            <form id="signup-form">
                <div class="form-group">
                    <label for="email">Email</label>
                    <input type="email" id="email" class="form-control" required>
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" class="form-control" required>
                </div>
                <button type="submit" class="btn btn-primary">Sign Up</button>
            </form>
            <p>Or <a href="#" id="show-login">login to your account</a>.</p>
        `;
        document.getElementById('signup-form').addEventListener('submit', handleSignup);
        document.getElementById('show-login').addEventListener('click', (e) => { e.preventDefault(); renderLoginForm(); });
    };

    const renderDashboard = (user) => {
        appRoot.innerHTML = `
            <h2>Welcome, ${user.email}</h2>
            <p>Your CCS Hyper dashboard is ready.</p>
            <button id="sync-schedule" class="btn btn-primary">Sync CCS Schedule</button>
            <button id="google-sync" class="btn btn-google">Sync with Google Calendar</button>
            <button id="logout" class="btn">Logout</button>
        `;
        document.getElementById('logout').addEventListener('click', handleLogout);
        // Add event listeners for other buttons
    };

    const handleLogin = async (e) => {
        e.preventDefault();
        const email = e.target.email.value;
        const password = e.target.password.value;
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) alert(error.message);
    };

    const handleSignup = async (e) => {
        e.preventDefault();
        const email = e.target.email.value;
        const password = e.target.password.value;
        const { error } = await supabase.auth.signUp({ email, password });
        if (error) alert(error.message); else alert('Check your email for a confirmation link!');
    };

    const handleLogout = async () => {
        await supabase.auth.signOut();
    };

    // Main logic
    showLoading(true);
    supabase.auth.onAuthStateChange((event, session) => {
        showLoading(false);
        if (session) {
            renderDashboard(session.user);
        } else {
            renderLoginForm();
        }
    });
});
