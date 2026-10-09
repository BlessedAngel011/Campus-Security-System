package com.campus.security.service;

import com.campus.security.model.Administrator;
import com.campus.security.model.VerificationCode;
import com.campus.security.model.AlertAssignment;
import com.campus.security.model.User;
import com.campus.security.model.SecurityOfficer;
import com.campus.security.model.EmergencyAlert;
import com.campus.security.model.Campus;
import com.campus.security.model.IncidentReport;

import com.campus.security.repository.AdministratorRepository;
import com.campus.security.repository.VerificationCodeRepository;
import com.campus.security.repository.UserRepository;
import com.campus.security.repository.SecurityOfficerRepository;
import com.campus.security.repository.EmergencyAlertRepository;
import com.campus.security.repository.IncidentReportRepository;
import com.campus.security.repository.CampusRepository;
import com.campus.security.repository.AlertAssignmentRepository;

import com.campus.security.dto.OfficerWorkloadResponse;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.beans.factory.annotation.Value;

import java.time.LocalDateTime;
import java.security.SecureRandom;
import java.security.MessageDigest;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.List;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.Map;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

@Service
public class AdminService {

    private final AdministratorRepository administratorRepository;
    private final VerificationCodeRepository verificationCodeRepository;
    private final UserRepository userRepository;
    private final SecurityOfficerRepository officerRepository;
    private final EmergencyAlertRepository emergencyRepository;
    private final IncidentReportRepository incidentRepository;
    private final CampusRepository campusRepository;
    private final UserService userService;
    private final OfficerService officerService;
    private final AlertAssignmentRepository assignmentRepository;
    private final EmailService emailService;

    @Value("${app.admin.token-secret:change-this-admin-secret-before-production}")
    private String tokenSecret;

    public AdminService(
            AdministratorRepository administratorRepository,
            VerificationCodeRepository verificationCodeRepository,
            UserRepository userRepository,
            SecurityOfficerRepository officerRepository,
            EmergencyAlertRepository emergencyRepository,
            IncidentReportRepository incidentRepository,
            CampusRepository campusRepository,
            UserService userService,
            OfficerService officerService,
            AlertAssignmentRepository assignmentRepository,
            EmailService emailService) {

        this.administratorRepository = administratorRepository;
        this.verificationCodeRepository = verificationCodeRepository;
        this.userRepository = userRepository;
        this.officerRepository = officerRepository;
        this.emergencyRepository = emergencyRepository;
        this.incidentRepository = incidentRepository;
        this.campusRepository = campusRepository;
        this.userService = userService;
        this.officerService = officerService;
        this.assignmentRepository = assignmentRepository;
        this.emailService = emailService;
    }

    // =========================================================
    // 1. VERIFY ADMINISTRATOR DETAILS
    // =========================================================

    public Administrator verifyAdminDetails(
            String employeeNumber,
            String universityEmail) {

        Administrator admin =
                administratorRepository
                        .findByEmployeeNumber(employeeNumber)
                        .orElseThrow(() ->
                                new RuntimeException(
                                        "Administrator employee number not found."
                                )
                        );

        if (!admin.getUniversityEmail()
                .equalsIgnoreCase(universityEmail)) {

            throw new RuntimeException(
                    "University email does not match the employee number."
            );
        }

        return admin;
    }

    // =========================================================
    // 2. GENERATE VERIFICATION CODE
    // =========================================================

    public VerificationCode generateVerificationCode(
            String employeeNumber,
            String universityEmail) {

        Administrator admin =
                verifyAdminDetails(
                        employeeNumber,
                        universityEmail
                );

        String code =
                String.format(
                        "%06d",
                        new SecureRandom().nextInt(1000000)
                );

        VerificationCode verificationCode =
                new VerificationCode();

        verificationCode.setAdministrator(admin);
        verificationCode.setVerificationCode(code);

        verificationCode.setExpiresAt(
                LocalDateTime.now().plusMinutes(10)
        );

        verificationCode.setUsed(false);

        verificationCode.setCreatedAt(
                LocalDateTime.now()
        );

        VerificationCode savedCode =
                verificationCodeRepository.save(verificationCode);

        String otpAddress = admin.getPersonalEmail() == null || admin.getPersonalEmail().isBlank()
                ? admin.getUniversityEmail() : admin.getPersonalEmail();
        emailService.sendOtp(otpAddress, code, "administrator sign-in");
        return savedCode;
    }

    // =========================================================
    // 3. CONFIRM VERIFICATION CODE
    // =========================================================

    public Administrator confirmVerificationCode(
            String employeeNumber,
            String code) {

        Administrator admin =
                administratorRepository
                        .findByEmployeeNumber(employeeNumber)
                        .orElseThrow(() ->
                                new RuntimeException(
                                        "Administrator not found."
                                )
                        );

        VerificationCode verificationCode =
                verificationCodeRepository
                        .findByVerificationCode(code)
                        .orElseThrow(() ->
                                new RuntimeException(
                                        "Invalid verification code."
                                )
                        );

        if (!verificationCode
                .getAdministrator()
                .getAdminId()
                .equals(admin.getAdminId())) {

            throw new RuntimeException(
                    "Verification code does not belong to this administrator."
            );
        }

        if (verificationCode.getUsed()) {

            throw new RuntimeException(
                    "Verification code has already been used."
            );
        }

        if (verificationCode
                .getExpiresAt()
                .isBefore(LocalDateTime.now())) {

            throw new RuntimeException(
                    "Verification code has expired."
            );
        }

        verificationCode.setUsed(true);

        verificationCodeRepository.save(
                verificationCode
        );

        admin.setVerificationStatus(
                Administrator.VerificationStatus.VERIFIED
        );

        return administratorRepository.save(admin);
    }

    // =========================================================
    // ADMIN SESSION
    // =========================================================

    public String createSessionToken(Administrator admin) {

        long expiry =
                System.currentTimeMillis()
                        + (8L * 60 * 60 * 1000);

        String payload =
                admin.getAdminId()
                        + ":"
                        + expiry;

        return Base64.getUrlEncoder()
                .withoutPadding()
                .encodeToString(
                        payload.getBytes(
                                StandardCharsets.UTF_8))
                + "."
                + sign(payload);
    }

    public Administrator getAdminFromToken(String token) {

        try {

            String[] parts =
                    token.split("\\.");

            if (parts.length != 2) {
                throw new RuntimeException(
                        "Invalid administrator session.");
            }

            String payload =
                    new String(
                            Base64.getUrlDecoder()
                                    .decode(parts[0]),
                            StandardCharsets.UTF_8);

            if (!MessageDigest.isEqual(
                    sign(payload)
                            .getBytes(StandardCharsets.UTF_8),
                    parts[1]
                            .getBytes(StandardCharsets.UTF_8))) {

                throw new RuntimeException(
                        "Invalid administrator session.");
            }

            String[] values =
                    payload.split(":");

            if (values.length != 2) {
                throw new RuntimeException(
                        "Invalid administrator session.");
            }

            if (Long.parseLong(values[1])
                    < System.currentTimeMillis()) {

                throw new RuntimeException(
                        "Administrator session has expired.");
            }

            Administrator admin =
                    administratorRepository
                            .findById(
                                    Integer.parseInt(values[0]))
                            .orElseThrow(() ->
                                    new RuntimeException(
                                            "Administrator not found."));

            if (admin.getVerificationStatus()
                    != Administrator.VerificationStatus.VERIFIED) {

                throw new RuntimeException(
                        "Administrator is not verified.");
            }

            return admin;

        } catch (RuntimeException e) {

            throw e;

        } catch (Exception e) {

            throw new RuntimeException(
                    "Invalid administrator session.");
        }
    }

    private String sign(String value) {

        try {

            Mac mac =
                    Mac.getInstance("HmacSHA256");

            mac.init(
                    new SecretKeySpec(
                            tokenSecret.getBytes(
                                    StandardCharsets.UTF_8),
                            "HmacSHA256"));

            return Base64.getUrlEncoder()
                    .withoutPadding()
                    .encodeToString(
                            mac.doFinal(
                                    value.getBytes(
                                            StandardCharsets.UTF_8)));

        } catch (Exception e) {

            throw new RuntimeException(
                    "Could not create administrator session.");
        }
    }

    // =========================================================
    // DASHBOARD
    // =========================================================

    public Map<String, Long> getDashboardStats() {

        return Map.of(
                "users",
                userRepository.count(),

                "officers",
                officerRepository.count(),

                "activeEmergencies",
                (long) emergencyRepository
                        .findByAlertStatus(
                                EmergencyAlert.AlertStatus.SENT)
                        .size(),

                "openIncidents",
                (long) incidentRepository
                        .findByIncidentStatus(
                                IncidentReport.IncidentStatus.REPORTED)
                        .size()
        );
    }

    // =========================================================
    // USERS AND OFFICERS
    // =========================================================

    public List<User> getUsers() {

        return userRepository.findAll();
    }

    public List<SecurityOfficer> getOfficers() {

        return officerRepository.findAll();
    }

    // =========================================================
    // ADMINISTRATOR ACCOUNT MANAGEMENT
    // =========================================================

    public List<Administrator> getAdministrators() {
        return administratorRepository.findAll();
    }

    @Transactional
    public Administrator createAdministrator(
            String firstName,
            String lastName,
            String employeeNumber,
            String universityEmail,
            String personalEmail,
            String phoneNumber,
            Integer campusId) {

        firstName = requireText(firstName, "First name");
        lastName = requireText(lastName, "Last name");
        employeeNumber = requireText(employeeNumber, "Employee number");
        universityEmail = requireText(universityEmail, "University email").toLowerCase();
        personalEmail = requireText(personalEmail, "Personal Gmail").toLowerCase();

        if (!universityEmail.endsWith("@ufh.ac.za")) {
            throw new RuntimeException("Administrator email must be a UFH email address ending in @ufh.ac.za.");
        }
        if (administratorRepository.findByEmployeeNumber(employeeNumber).isPresent()) {
            throw new RuntimeException("An administrator with this employee number already exists.");
        }
        if (!personalEmail.endsWith("@gmail.com")) {
            throw new RuntimeException("Administrator personal email must be a Gmail address ending in @gmail.com.");
        }
        if (administratorRepository.findByPersonalEmail(personalEmail).isPresent()) {
            throw new RuntimeException("An administrator with this personal Gmail already exists.");
        }
        if (administratorRepository.findByUniversityEmail(universityEmail).isPresent()) {
            throw new RuntimeException("An administrator with this university email already exists.");
        }

        Campus campus = campusRepository.findById(campusId)
                .orElseThrow(() -> new RuntimeException("Campus not found."));

        Administrator admin = new Administrator();
        admin.setFirstName(firstName);
        admin.setLastName(lastName);
        admin.setEmployeeNumber(employeeNumber);
        admin.setUniversityEmail(universityEmail);
        admin.setPersonalEmail(personalEmail);
        admin.setPhoneNumber(phoneNumber == null || phoneNumber.isBlank() ? null : phoneNumber.trim());
        admin.setCampus(campus);
        admin.setVerificationStatus(Administrator.VerificationStatus.PENDING);

        Administrator saved = administratorRepository.save(admin);
        // Send the first OTP immediately. The administrator can also request a new
        // code from the normal admin sign-in screen after the resend interval.
        generateVerificationCode(saved.getEmployeeNumber(), saved.getUniversityEmail());
        return saved;
    }

    private String requireText(String value, String label) {
        if (value == null || value.isBlank()) {
            throw new RuntimeException(label + " is required.");
        }
        return value.trim();
    }

    // =========================================================
    // OFFICER WORKLOAD
    // =========================================================

    public List<OfficerWorkloadResponse> getOfficerWorkloads() {

        return officerRepository.findAll()
                .stream()
                .map(this::buildOfficerWorkload)
                .toList();
    }

    private OfficerWorkloadResponse buildOfficerWorkload(
            SecurityOfficer officer) {

        List<OfficerWorkloadResponse.WorkItem> cases =
                new ArrayList<>();

        List<AlertAssignment.AssignmentStatus>
                activeAssignmentStatuses =
                List.of(
                        AlertAssignment.AssignmentStatus.ASSIGNED,
                        AlertAssignment.AssignmentStatus.ACCEPTED,
                        AlertAssignment.AssignmentStatus.RESPONDING
                );

        assignmentRepository
                .findByOfficerAndAssignmentStatusInOrderByAssignedAtDesc(
                        officer,
                        activeAssignmentStatuses)
                .forEach(assignment -> {

                    EmergencyAlert emergency =
                            assignment.getEmergencyAlert();

                    User reporter =
                            emergency.getUser();

                    String location =
                            emergency.getLocation() != null
                                    ? emergency.getLocation()
                                      .getLocationName()
                                    : formatGps(
                                    emergency.getLatitude(),
                                    emergency.getLongitude());

                    cases.add(
                            new OfficerWorkloadResponse.WorkItem(
                                    "EMERGENCY",
                                    emergency.getEmergencyId(),
                                    emergency.getEmergencyType(),
                                    assignment
                                            .getAssignmentStatus()
                                            .name(),
                                    location,
                                    fullName(reporter),
                                    reporter == null
                                            ? null
                                            : reporter
                                              .getStudentStaffNumber(),
                                    assignment.getAssignedAt(),
                                    emergency.getResolvedAt()
                                            != null
                                            ? emergency.getResolvedAt()
                                            : emergency.getCreatedAt()
                            )
                    );
                });

        incidentRepository
                .findByAssignedOfficerOrderByReportedAtDesc(
                        officer)
                .stream()
                .filter(incident ->
                        incident.getIncidentStatus()
                                != IncidentReport
                                .IncidentStatus.RESOLVED
                                && incident.getIncidentStatus()
                                != IncidentReport
                                .IncidentStatus.CLOSED)
                .forEach(incident -> {

                    User reporter =
                            incident.getUser();

                    cases.add(
                            new OfficerWorkloadResponse.WorkItem(
                                    "INCIDENT",
                                    incident.getIncidentId(),
                                    incident.getIncidentType(),
                                    incident
                                            .getIncidentStatus()
                                            .name(),
                                    incident.getLocation() == null
                                            ? "Location unavailable"
                                            : incident.getLocation()
                                              .getLocationName(),
                                    fullName(reporter),
                                    reporter == null
                                            ? null
                                            : reporter
                                              .getStudentStaffNumber(),
                                    incident.getAssignedAt(),
                                    incident.getLastUpdatedAt()
                                            != null
                                            ? incident
                                              .getLastUpdatedAt()
                                            : incident
                                              .getReportedAt()
                            )
                    );
                });

        cases.sort(
                Comparator.comparing(
                        OfficerWorkloadResponse.WorkItem::startedAt,
                        Comparator.nullsLast(
                                Comparator.reverseOrder()
                        )
                )
        );

        return new OfficerWorkloadResponse(
                officer.getOfficerId(),
                officer.getFirstName(),
                officer.getLastName(),
                officer.getEmployeeNumber(),
                officer.getPhoneNumber(),
                officer.getCampus() == null
                        ? "Campus unavailable"
                        : officer.getCampus()
                          .getCampusName(),
                officer.getAvailabilityStatus(),
                cases.size(),
                cases
        );
    }

    // =========================================================
    // HELPER METHODS
    // =========================================================

    private String fullName(User user) {

        if (user == null) {
            return "Unknown user";
        }

        return (
                user.getFirstName()
                        + " "
                        + user.getLastName()
        ).trim();
    }

    private String formatGps(
            Double latitude,
            Double longitude) {

        if (latitude == null
                || longitude == null) {

            return "Location unavailable";
        }

        return String.format(
                "GPS %.5f, %.5f",
                latitude,
                longitude);
    }

    // =========================================================
    // ADMIN DATA
    // =========================================================

    public List<EmergencyAlert> getEmergencies() {
        List<EmergencyAlert> alerts = emergencyRepository.findAll();
        for (EmergencyAlert alert : alerts) {
            assignmentRepository.findTopByEmergencyAlertOrderByAssignedAtDesc(alert)
                    .ifPresent(a -> alert.setAssignedOfficer(a.getOfficer()));
        }
        return alerts;
    }

    public List<IncidentReport> getIncidents() {

        return incidentRepository
                .findAllByOrderByReportedAtDesc();
    }

    public List<Campus> getCampuses() {

        return campusRepository.findAll();
    }

    // =========================================================
    // CREATE SECURITY OFFICER
    // =========================================================

    @Transactional
    public SecurityOfficer createOfficer(
            String firstName,
            String lastName,
            String employeeNumber,
            String password,
            String phoneNumber,
            Integer campusId) {

        if (password == null
                || password.length() < 8) {

            throw new RuntimeException(
                    "The temporary password must contain at least 8 characters.");
        }

        userService.registerUser(
                employeeNumber,
                password,
                firstName,
                lastName,
                phoneNumber,
                "SECURITY_OFFICER",
                campusId
        );

        return officerService.addOfficer(
                firstName,
                lastName,
                employeeNumber,
                employeeNumber + "@ufh.ac.za",
                phoneNumber,
                campusId
        );
    }

    // =========================================================
    // UPDATE USER STATUS
    // =========================================================

    public User updateUserStatus(
            Integer userId,
            User.AccountStatus status) {

        User user =
                userRepository
                        .findById(userId)
                        .orElseThrow(() ->
                                new RuntimeException(
                                        "User not found."));

        user.setAccountStatus(status);

        return userRepository.save(user);
    }
}