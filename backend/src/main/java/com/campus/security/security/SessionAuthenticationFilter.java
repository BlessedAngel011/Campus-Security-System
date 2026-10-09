package com.campus.security.security;

import com.campus.security.model.Administrator;
import com.campus.security.model.User;
import com.campus.security.service.AdminService;
import com.campus.security.service.UserService;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.List;

@Component
public class SessionAuthenticationFilter
        extends OncePerRequestFilter {

    private final UserService userService;
    private final AdminService adminService;

    public SessionAuthenticationFilter(
            UserService userService,
            AdminService adminService) {

        this.userService = userService;
        this.adminService = adminService;
    }

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain)
            throws ServletException, IOException {

        String authorizationHeader =
                request.getHeader("Authorization");

        if (authorizationHeader != null
                && authorizationHeader.startsWith("Bearer ")) {

            String sessionToken =
                    authorizationHeader
                            .substring(7)
                            .trim();

            if (!sessionToken.isBlank()) {
                authenticateMobileUser(sessionToken);

                if (SecurityContextHolder
                        .getContext()
                        .getAuthentication() == null) {

                    authenticateAdministrator(sessionToken);
                }
            }
        }

        filterChain.doFilter(request, response);
    }

    private void authenticateMobileUser(
            String sessionToken) {

        try {
            User user =
                    userService.getUserFromSession(
                            sessionToken
                    );

            String roleName =
                    normaliseRole(
                            user.getRole().getRoleName()
                    );

            SimpleGrantedAuthority authority =
                    new SimpleGrantedAuthority(
                            "ROLE_" + roleName
                    );

            UsernamePasswordAuthenticationToken authentication =
                    new UsernamePasswordAuthenticationToken(
                            user,
                            null,
                            List.of(authority)
                    );

            SecurityContextHolder
                    .getContext()
                    .setAuthentication(authentication);

        } catch (RuntimeException exception) {
            SecurityContextHolder.clearContext();
        }
    }

    private void authenticateAdministrator(
            String sessionToken) {

        try {
            Administrator administrator =
                    adminService.getAdminFromToken(
                            sessionToken
                    );

            SimpleGrantedAuthority authority =
                    new SimpleGrantedAuthority(
                            "ROLE_ADMIN"
                    );

            UsernamePasswordAuthenticationToken authentication =
                    new UsernamePasswordAuthenticationToken(
                            administrator,
                            null,
                            List.of(authority)
                    );

            SecurityContextHolder
                    .getContext()
                    .setAuthentication(authentication);

        } catch (RuntimeException exception) {
            SecurityContextHolder.clearContext();
        }
    }

    private String normaliseRole(String roleName) {
        String normalised = roleName == null
                ? ""
                : roleName
                  .trim()
                  .replace(" ", "_")
                  .replace("-", "_")
                  .toUpperCase();

        /*
         * Support older officer role names that might
         * already exist in the database.
         */
        if (normalised.equals("SECURITY")
                || normalised.equals("OFFICER")
                || normalised.equals("SECURITYOFFICER")) {

            return "SECURITY_OFFICER";
        }

        return normalised;
    }
}