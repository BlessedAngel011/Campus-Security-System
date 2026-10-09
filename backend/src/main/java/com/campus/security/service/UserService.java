package com.campus.security.service;

import com.campus.security.model.*;
import com.campus.security.repository.*;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.security.SecureRandom;
import java.time.LocalDateTime;
import java.util.UUID;
import java.util.regex.Pattern;

@Service
public class UserService {
    private static final Pattern UFH_EMAIL = Pattern.compile("^[A-Za-z0-9._%+-]+@ufh\\.ac\\.za$", Pattern.CASE_INSENSITIVE);
    private static final Pattern GMAIL_EMAIL = Pattern.compile("^[A-Za-z0-9._%+-]+@gmail\\.com$", Pattern.CASE_INSENSITIVE);
    private final UserRepository userRepository;
    private final UserSessionRepository userSessionRepository;
    private final RoleRepository roleRepository;
    private final CampusRepository campusRepository;
    private final UserVerificationCodeRepository codeRepository;
    private final PasswordEncoder passwordEncoder;
    private final EmailService emailService;
    private final SecureRandom secureRandom = new SecureRandom();

    public UserService(UserRepository userRepository, UserSessionRepository userSessionRepository,
            RoleRepository roleRepository, CampusRepository campusRepository,
            UserVerificationCodeRepository codeRepository, PasswordEncoder passwordEncoder,
            EmailService emailService) {
        this.userRepository = userRepository;
        this.userSessionRepository = userSessionRepository;
        this.roleRepository = roleRepository;
        this.campusRepository = campusRepository;
        this.codeRepository = codeRepository;
        this.passwordEncoder = passwordEncoder;
        this.emailService = emailService;
    }

    // Compatibility overload used by administrator-created officer accounts.
    @Transactional
    public User registerUser(String username, String password, String firstName, String lastName,
            String phoneNumber, String roleName, Integer campusId) {
        return registerUser(username, username + "@ufh.ac.za", null, password, firstName, lastName,
                phoneNumber, roleName, campusId, true);
    }

    @Transactional
    public User registerUser(String username, String email, String personalEmail, String password, String firstName,
            String lastName, String phoneNumber, String roleName, Integer campusId) {
        return registerUser(username, email, personalEmail, password, firstName, lastName, phoneNumber,
                roleName, campusId, false);
    }

    private User registerUser(String username, String email, String personalEmail, String password, String firstName,
            String lastName, String phoneNumber, String roleName, Integer campusId,
            boolean trustedOfficerCreation) {
        username = username == null ? "" : username.trim();
        email = normaliseEmail(email);
        personalEmail = normaliseEmail(personalEmail);
        if (username.isBlank()) throw new RuntimeException("Student/staff number is required.");
        if (password == null || password.length() < 8) throw new RuntimeException("Password must contain at least 8 characters.");
        if (userRepository.existsByStudentStaffNumber(username)) throw new RuntimeException("Student/staff number already exists.");
        if (!UFH_EMAIL.matcher(email).matches()) throw new RuntimeException("Enter a valid @ufh.ac.za university email address.");
        if (userRepository.existsByEmailIgnoreCase(email)) throw new RuntimeException("University email is already registered.");
        if (!trustedOfficerCreation) {
            if (!GMAIL_EMAIL.matcher(personalEmail).matches()) throw new RuntimeException("Enter a valid personal Gmail address ending in @gmail.com.");
            if (userRepository.existsByPersonalEmailIgnoreCase(personalEmail)) throw new RuntimeException("Personal Gmail address is already registered.");
        }

        String normalRole = normaliseRole(roleName);
        if (normalRole.equals("STUDENT")) {
            String expected = (username + "@ufh.ac.za").toLowerCase();
            if (!email.equals(expected)) throw new RuntimeException("Student email must be your student number followed by @ufh.ac.za.");
        }

        Role role = roleRepository.findByRoleNameIgnoreCase(roleName)
                .orElseGet(() -> roleRepository.findAll().stream()
                        .filter(item -> normaliseRole(item.getRoleName()).equals(normalRole))
                        .findFirst().orElseThrow(() -> new RuntimeException("Role not found: " + roleName)));
        Campus campus = campusRepository.findById(campusId)
                .orElseThrow(() -> new RuntimeException("Campus not found: " + campusId));

        User user = new User();
        user.setStudentStaffNumber(username);
        user.setFirstName(firstName);
        user.setLastName(lastName);
        user.setPhoneNumber(phoneNumber);
        user.setEmail(email);
        user.setPersonalEmail(personalEmail.isBlank() ? null : personalEmail);
        user.setEmailVerified(trustedOfficerCreation ? true : false);
        user.setPasswordHash(passwordEncoder.encode(password));
        user.setRole(role);
        user.setCampus(campus);
        user.setAccountStatus(User.AccountStatus.ACTIVE);
        user.setEmergencyButtonEnabled(true);
        user.setFalseAlertCount(0);
        user = userRepository.save(user);

        if (!trustedOfficerCreation) sendUserCode(user, UserVerificationCode.Purpose.EMAIL_VERIFICATION);
        return user;
    }

    @Transactional
    public void resendRegistrationCode(String email) {
        User user = findByEmail(email);
        if (Boolean.TRUE.equals(user.getEmailVerified())) return;
        sendUserCode(user, UserVerificationCode.Purpose.EMAIL_VERIFICATION);
    }

    @Transactional
    public void verifyRegistration(String email, String code) {
        User user = findByEmail(email);
        consumeCode(user, UserVerificationCode.Purpose.EMAIL_VERIFICATION, code);
        user.setEmailVerified(true);
        userRepository.save(user);
    }

    @Transactional
    public void requestPasswordReset(String email) {
        // Controller intentionally returns the same message whether the address exists or not.
        userRepository.findByPersonalEmailIgnoreCase(normaliseEmail(email)).ifPresent(user ->
                sendUserCode(user, UserVerificationCode.Purpose.PASSWORD_RESET));
    }

    @Transactional
    public void resetPassword(String email, String code, String newPassword) {
        if (newPassword == null || newPassword.length() < 8)
            throw new RuntimeException("New password must contain at least 8 characters.");
        User user = findByPersonalEmail(email);
        consumeCode(user, UserVerificationCode.Purpose.PASSWORD_RESET, code);
        user.setPasswordHash(passwordEncoder.encode(newPassword));
        userRepository.save(user);
        userSessionRepository.findAll().stream().filter(s -> s.getUser().getUserId().equals(user.getUserId()))
                .forEach(s -> { s.setActive(false); userSessionRepository.save(s); });
    }

    private void sendUserCode(User user, UserVerificationCode.Purpose purpose) {
        codeRepository.findTopByUserAndPurposeAndUsedFalseOrderByCreatedAtDesc(user, purpose).ifPresent(previous -> {
            if (previous.getCreatedAt() != null && previous.getCreatedAt().isAfter(LocalDateTime.now().minusSeconds(60)))
                throw new RuntimeException("Please wait 60 seconds before requesting another code.");
        });
        String code = String.format("%06d", secureRandom.nextInt(1_000_000));
        UserVerificationCode item = new UserVerificationCode();
        item.setUser(user); item.setCode(code); item.setPurpose(purpose);
        item.setCreatedAt(LocalDateTime.now()); item.setExpiresAt(LocalDateTime.now().plusMinutes(10)); item.setUsed(false);
        codeRepository.save(item);
        String otpAddress = user.getPersonalEmail() == null || user.getPersonalEmail().isBlank()
                ? user.getEmail() : user.getPersonalEmail();
        emailService.sendOtp(otpAddress, code,
                purpose == UserVerificationCode.Purpose.PASSWORD_RESET ? "password reset" : "email verification");
    }

    private void consumeCode(User user, UserVerificationCode.Purpose purpose, String code) {
        UserVerificationCode item = codeRepository.findTopByUserAndPurposeAndUsedFalseOrderByCreatedAtDesc(user, purpose)
                .orElseThrow(() -> new RuntimeException("No active verification code was found."));
        if (item.getExpiresAt().isBefore(LocalDateTime.now())) throw new RuntimeException("Verification code has expired.");
        if (code == null || !item.getCode().equals(code.trim())) throw new RuntimeException("Invalid verification code.");
        item.setUsed(true); codeRepository.save(item);
    }

    private User findByEmail(String email) {
        return userRepository.findByEmailIgnoreCase(normaliseEmail(email))
                .orElseThrow(() -> new RuntimeException("No account was found for that university email."));
    }
    private User findByPersonalEmail(String email) {
        return userRepository.findByPersonalEmailIgnoreCase(normaliseEmail(email))
                .orElseThrow(() -> new RuntimeException("No account was found for that personal email."));
    }
    private String normaliseEmail(String email) { return email == null ? "" : email.trim().toLowerCase(); }
    private String normaliseRole(String roleName) { return roleName == null ? "" : roleName.trim().replace(" ", "_").replace("-", "_").toUpperCase(); }

    @Transactional
    public UserSession login(String username, String password, String deviceId, String ipAddress) {
        User user = userRepository.findByStudentStaffNumber(username)
                .orElseThrow(() -> new RuntimeException("Invalid student/staff number or password."));
        if (user.getAccountStatus() != User.AccountStatus.ACTIVE) throw new RuntimeException("User account is not active.");
        if (Boolean.FALSE.equals(user.getEmailVerified())) throw new RuntimeException("Verify your account with the OTP sent to your personal email before signing in.");
        if (!passwordEncoder.matches(password, user.getPasswordHash())) throw new RuntimeException("Invalid student/staff number or password.");
        String sessionToken = UUID.randomUUID().toString();
        UserSession session = new UserSession();
        session.setUser(user); session.setSessionToken(sessionToken); session.setDeviceId(deviceId); session.setIpAddress(ipAddress);
        session.setLoginTime(LocalDateTime.now()); session.setExpiryTime(LocalDateTime.now().plusDays(30)); session.setActive(true);
        return userSessionRepository.save(session);
    }

    @Transactional
    public void logout(String sessionToken) {
        UserSession session = userSessionRepository.findBySessionToken(sessionToken)
                .orElseThrow(() -> new RuntimeException("Session not found."));
        session.setActive(false); userSessionRepository.save(session);
    }

    @Transactional
    public User getUserFromSession(String sessionToken) {
        UserSession session = userSessionRepository.findBySessionToken(sessionToken)
                .orElseThrow(() -> new RuntimeException("Session not found."));
        if (!Boolean.TRUE.equals(session.getActive())) throw new RuntimeException("Session is no longer active.");
        if (session.getExpiryTime().isBefore(LocalDateTime.now())) {
            session.setActive(false); userSessionRepository.save(session); throw new RuntimeException("Session has expired.");
        }
        User user = session.getUser(); user.getRole().getRoleName(); user.getCampus().getCampusId(); return user;
    }
}
