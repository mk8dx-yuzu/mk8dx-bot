package org.kevnkkm;

import java.util.ArrayList;
import java.util.Arrays;

public class Main {

  public static void getFairestTeams(ArrayList<Integer> playerList, int teamsize) {

    int playerCount = playerList.size();
    int teamCount = playerCount / teamsize;

    System.out.println("Player Count: " + playerCount);
    System.out.println("Team Count: " + teamCount);
    System.out.println("--------------------");

    // Sort the player list in descending order
    playerList.sort((a, b) -> b - a);

    // Create team array variables
    ArrayList<ArrayList<Integer>> teams = new ArrayList<>();
    for (int i = 0; i < teamCount; i++) {
      teams.add(new ArrayList<>());
    }

    // Distribute players to teams in a balanced fashion (greedy approach)
    boolean reverse = false;
    int teamIndex = 0;
    for (int i = 0; i < playerCount; i++) {
      teams.get(teamIndex).add(playerList.get(i));

      if (!reverse) {
        teamIndex++;
        if (teamIndex == teamCount) {
          teamIndex--;
          reverse = true;
        }
      } else {
        teamIndex--;
        if (teamIndex == -1) {
          teamIndex++;
          reverse = false;
        }
      }
    }

    // Print the teams
    for (int i = 0; i < teamCount; i++) {
      System.out.println("Team " + (i + 1) + ": " + teams.get(i) + " (Total MMR: " + teams.get(i).stream().mapToInt(Integer::intValue).sum() + ")");
    }
  }

  public static void main(String[] args) {

    ArrayList<Integer> playerList = new ArrayList<>(Arrays.asList(
        5868, 10351, 9825, 7152, 3088, 1768, 2400, 3087, 6070, 1500, 5678, 3088
    ));

    getFairestTeams(playerList, 6);
    System.out.println("--------------------");
    getFairestTeams(playerList, 4);
    System.out.println("--------------------");
    getFairestTeams(playerList, 3);
    System.out.println("--------------------");
    getFairestTeams(playerList, 2);
    System.out.println("--------------------");
  }
}