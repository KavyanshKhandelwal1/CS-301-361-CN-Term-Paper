% --- Simulation Parameters ---
frequency = 10; % Transmission frequency in kHz
distance = 1:1:5000; % Transmission distance vector from 1m to 5km
spreading_factor = 1.5; % Spreading factor (k)
shipping_activity = 0.5; % Shipping activity factor (s, 0 to 1)
wind_speed = 5; % Wind speed in m/s
source_level = 180; % Source Level in dB re 1 uPa
bandwidth = 3; % Bandwidth in kHz

% --- 1. Calculate Absorption Coefficient (Thorp's formula) ---
% This formula provides an empirical fit for absorption in dB/km.
alpha_dB_per_km = (0.11 * (frequency^2) / (1 + frequency^2)) +...
                  (44 * (frequency^2) / (4100 + frequency^2)) +...
                  (2.75e-4 * frequency^2) + 0.003;

% --- 2. Calculate Transmission Loss (TL) in dB ---
% TL(d,f) = k * 10 * log10(d) + d_km * alpha_dB_per_km
transmission_loss = spreading_factor * 10 * log10(distance) +...
                    (distance / 1000).* alpha_dB_per_km;

% --- 3. Calculate Ambient Noise Level (NL) in dB ---
% Power Spectral Densities (PSDs) in dB/Hz
N_shipping_psd = 40 + 20*(shipping_activity - 0.5) + ...
    26*log10(frequency) - 60*log10(frequency + 0.03);
N_waves_psd = 50 + 7.5*sqrt(wind_speed) + ...
    20*log10(frequency) - 40*log10(frequency + 0.4);
N_turbulence_psd = 27 - 30*log10(frequency);
N_thermal_psd = -27 + 20*log10(frequency);

% Convert PSDs from dB to linear scale, sum them, and convert back to dB
total_noise_linear = 10.^(N_shipping_psd/10) + ...
    10.^(N_waves_psd/10) + 10.^(N_turbulence_psd/10) + ...
    10.^(N_thermal_psd/10);
total_noise_psd_dB = 10*log10(total_noise_linear);

% Calculate total Noise Level by adding bandwidth factor
noise_level = total_noise_psd_dB + 10*log10(bandwidth * 1000);

% --- 4. Calculate Signal-to-Noise Ratio (SNR) in dB ---
% SNR = Source Level - Transmission Loss - Noise Level
snr = source_level - transmission_loss - noise_level;

% --- 5. Generate Charts and Graphs ---
figure('Name', 'Underwater Acoustic Channel Simulation');

% Plot Transmission Loss
subplot(2,1,1);
plot(distance/1000, transmission_loss, 'b-', 'LineWidth', 1.5);
title('Transmission Loss (TL) vs. Distance');
xlabel('Distance (km)');
ylabel('Transmission Loss (dB)');
grid on;
legend('TL');

% Plot SNR
subplot(2,1,2);
plot(distance/1000, snr, 'r-', 'LineWidth', 1.5);
title('Signal-to-Noise Ratio (SNR) vs. Distance');
xlabel('Distance (km)');
ylabel('SNR (dB)');
grid on;
hold on;
% Add a detection threshold line for reference
detection_threshold = 10;
yline(detection_threshold, '--k', 'LineWidth', 1);
hold off;
legend('SNR', 'Threshold');

% --- 6. Display Key Values in a Table ---
fprintf('\n--- Channel Simulation Results (f = %.1f kHz) ---\n', frequency);
fprintf('Absorption Coefficient: %.4f dB/km\n', alpha_dB_per_km);
fprintf('Calculated Noise Level: %.2f dB\n', noise_level);
fprintf('--------------------------------------\n');
fprintf('| Distance (km) | TL (dB) | SNR (dB) |\n');
fprintf('--------------------------------------\n');
% Display values at 1 km intervals
for i = 1000:1000:length(distance)
    fprintf('| %-13.1f | %-9.2f | %-9.2f |\n', ...
    distance(i)/1000, transmission_loss(i), snr(i));
end
fprintf('--------------------------------------\n');