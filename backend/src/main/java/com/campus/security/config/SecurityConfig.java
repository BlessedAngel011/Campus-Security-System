package com.campus.security.config;

import com.campus.security.security.SessionAuthenticationFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    public SecurityFilterChain securityFilterChain(
            HttpSecurity http,
            SessionAuthenticationFilter sessionAuthenticationFilter)
            throws Exception {

        http
                .csrf(csrf -> csrf.disable())
                .cors(cors -> {})
                .addFilterBefore(
                        sessionAuthenticationFilter,
                        UsernamePasswordAuthenticationFilter.class)
                .authorizeHttpRequests(auth -> auth

                        // Public registration/login
                        .requestMatchers(
                                "/api/users/register",
                                "/api/users/login").permitAll()

                        // Public administrator website files. Authentication is
                        // still required by the protected /api/admin/** routes.
                        .requestMatchers(
                                "/",
                                "/admin",
                                "/admin/",
                                "/admin/**",
                                "/favicon.ico",
                                "/error").permitAll()

                        // Administrator verification is done before
                        // the protected admin area.
                        .requestMatchers(
                                "/api/admin/verify-details",
                                "/api/admin/send-code",
                                "/api/admin/confirm-code").permitAll()

                        // Admin management
                        .requestMatchers("/api/admin/**")
                        .hasRole("ADMIN")

                        // An administrator can add/manage officers.
                        // A security officer can manage their own operational data.
                        .requestMatchers(
                                "/api/officers",
                                "/api/officers/verify/**")
                        .hasAnyRole("ADMIN", "SECURITY_OFFICER")

                        .requestMatchers(
                                "/api/officers/*/availability",
                                "/api/officers/*/location",
                                "/api/officers/available",
                                "/api/officers/me",
                                "/api/officers/me/**")
                        .hasAnyRole("ADMIN", "SECURITY_OFFICER")

                        // False-alert review is an admin function.
                        .requestMatchers("/api/false-alerts/**")
                        .hasRole("ADMIN")

                        // Campus locations are used by the mobile incident form.
                        .requestMatchers("/api/locations/**", "/api/locations")
                        .hasAnyRole(
                                "ADMIN",
                                "SECURITY_OFFICER",
                                "STUDENT",
                                "STAFF")

                        // Incident creation/viewing belongs to authenticated users.
                        // Status changes and resolution are officer/admin functions.
                        .requestMatchers(
                                "/api/incidents/*/status",
                                "/api/incidents/*/resolve",
                                "/api/incidents/*/evidence")
                        .hasAnyRole("ADMIN", "SECURITY_OFFICER")

                        .requestMatchers(
                                "/api/incidents",
                                "/api/incidents/my-reports")
                        .hasAnyRole(
                                "ADMIN",
                                "SECURITY_OFFICER",
                                "STUDENT",
                                "STAFF")

                        .requestMatchers("/api/incidents/status/**")
                        .hasAnyRole("ADMIN", "SECURITY_OFFICER")

                        .requestMatchers("/api/incidents/officer/**")
                        .hasAnyRole("ADMIN", "SECURITY_OFFICER")

                        .requestMatchers("/api/notifications/officer/**")
                        .hasAnyRole("ADMIN", "SECURITY_OFFICER")

                        // Emergency creation is available to authenticated users.
                        .requestMatchers("/api/emergency/alert")
                        .hasAnyRole(
                                "ADMIN",
                                "SECURITY_OFFICER",
                                "STUDENT",
                                "STAFF")

                        // Emergency status changes are operational functions.
                        .requestMatchers("/api/emergency/*/status")
                        .hasAnyRole("ADMIN", "SECURITY_OFFICER")

                        .anyRequest().authenticated()
                );

        return http.build();
    }
}
