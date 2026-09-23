
package com.campus.security.security;

import com.campus.security.model.User;
import com.campus.security.service.UserService;
import com.campus.security.service.AdminService;
import com.campus.security.model.Administrator;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.List;

@Component
public class SessionAuthenticationFilter extends OncePerRequestFilter {

    private final UserService userService;
    private final AdminService adminService;

    public SessionAuthenticationFilter(UserService userService, AdminService adminService) {
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

        // Check whether the request contains:
        // Authorization: Bearer <session-token>
        if (authorizationHeader != null
                && authorizationHeader.startsWith("Bearer ")) {

            String sessionToken =
                    authorizationHeader.substring(7);

            try {

                // Find the user associated with the session token
                User user =
                        userService.getUserFromSession(sessionToken);

                String roleName = user.getRole().getRoleName()
                        .trim()
                        .replace(" ", "_")
                        .replace("-", "_")
                        .toUpperCase();

                // Spring Security hasRole("STUDENT") expects ROLE_STUDENT.
                UsernamePasswordAuthenticationToken authentication =
                        new UsernamePasswordAuthenticationToken(
                                user,
                                null,
                                List.of(new SimpleGrantedAuthority(
                                        "ROLE_" + roleName))
                        );

                // Store authentication in Spring Security
                SecurityContextHolder
                        .getContext()
                        .setAuthentication(authentication);

            } catch (RuntimeException e) {

                try {
                    Administrator admin = adminService.getAdminFromToken(sessionToken);
                    UsernamePasswordAuthenticationToken authentication =
                            new UsernamePasswordAuthenticationToken(admin, null,
                                    List.of(new SimpleGrantedAuthority("ROLE_ADMIN")));
                    SecurityContextHolder.getContext().setAuthentication(authentication);
                } catch (RuntimeException ignored) {

                // Invalid or expired session token.
                // The request continues and Spring Security
                // can decide whether authentication is required.
                SecurityContextHolder
                        .clearContext();
                }
            }
        }

        // Continue with the request
        filterChain.doFilter(request, response);
    }
}
